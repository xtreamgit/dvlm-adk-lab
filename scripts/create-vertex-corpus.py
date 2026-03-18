#!/usr/bin/env python3
"""
Create a Vertex AI RAG corpus and import PDF files from a GCS bucket.

Usage:
    python scripts/create-vertex-corpus.py \
        --project adk-rag-tt-488718 \
        --location us-west1 \
        --corpus-name adk-rag-span-corp1 \
        --bucket gs://adk-rag-span-corp1 \
        [--chunk-size 512] \
        [--chunk-overlap 100] \
        [--dry-run]

After this script runs, the next backend startup (or manual admin sync)
will automatically register the corpus in the database via CorpusSyncService.
"""

import argparse
import sys
import time


def main():
    parser = argparse.ArgumentParser(
        description="Create a Vertex AI RAG corpus and import files from GCS"
    )
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--location", required=True, help="GCP region (e.g. us-west1)")
    parser.add_argument("--corpus-name", required=True, help="Display name for the corpus")
    parser.add_argument("--bucket", required=True, help="GCS bucket URI (gs://bucket-name)")
    parser.add_argument("--chunk-size", type=int, default=512, help="Chunk size for embedding")
    parser.add_argument("--chunk-overlap", type=int, default=100, help="Chunk overlap for embedding")
    parser.add_argument("--embedding-model", default="publishers/google/models/text-embedding-005",
                        help="Embedding model to use")
    parser.add_argument("--embedding-rpm", type=int, default=1000,
                        help="Max embedding requests per minute")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    args = parser.parse_args()

    # Ensure bucket starts with gs://
    bucket = args.bucket if args.bucket.startswith("gs://") else f"gs://{args.bucket}"

    print()
    print("=" * 60)
    print("  Vertex AI RAG Corpus Creation & Import")
    print("=" * 60)
    print()
    print(f"  Project:         {args.project}")
    print(f"  Location:        {args.location}")
    print(f"  Corpus name:     {args.corpus_name}")
    print(f"  GCS bucket:      {bucket}")
    print(f"  Chunk size:      {args.chunk_size}")
    print(f"  Chunk overlap:   {args.chunk_overlap}")
    print(f"  Embedding model: {args.embedding_model}")
    print(f"  Embedding RPM:   {args.embedding_rpm}")
    if args.dry_run:
        print(f"\n  ⚠️  DRY RUN — no changes will be made")
    print()

    if args.dry_run:
        print("── Step 1: [DRY RUN] Would initialize Vertex AI")
        print("── Step 2: [DRY RUN] Would check if corpus exists")
        print("── Step 3: [DRY RUN] Would create corpus")
        print(f"── Step 4: [DRY RUN] Would import files from {bucket}")
        print("\n✅ Dry run complete")
        return

    # ── Step 1: Initialize Vertex AI ─────────────────────────────────────────
    print("── Step 1: Initialize Vertex AI")
    try:
        import google.auth
        import vertexai
        from vertexai import rag

        credentials, _ = google.auth.default()
        vertexai.init(project=args.project, location=args.location, credentials=credentials)
        print(f"  ✅ Vertex AI initialized (project={args.project}, location={args.location})")
    except Exception as e:
        print(f"  ❌ Failed to initialize Vertex AI: {e}")
        sys.exit(1)

    # ── Step 2: Check if corpus already exists ───────────────────────────────
    print("\n── Step 2: Check if corpus already exists")
    existing_corpus = None
    try:
        corpora = list(rag.list_corpora())
        for corpus in corpora:
            if corpus.display_name == args.corpus_name:
                existing_corpus = corpus
                break

        if existing_corpus:
            print(f"  ℹ️  Corpus '{args.corpus_name}' already exists: {existing_corpus.name}")
            print(f"     Will skip creation and proceed to import.")
        else:
            print(f"  ℹ️  Corpus '{args.corpus_name}' does not exist yet — will create it")
            print(f"     Found {len(corpora)} existing corpora in project")
    except Exception as e:
        print(f"  ❌ Failed to list corpora: {e}")
        sys.exit(1)

    # ── Step 3: Create corpus ────────────────────────────────────────────────
    if not existing_corpus:
        print(f"\n── Step 3: Create corpus '{args.corpus_name}'")
        try:
            embedding_model_config = rag.RagEmbeddingModelConfig(
                vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                    publisher_model=args.embedding_model
                )
            )

            rag_corpus = rag.create_corpus(
                display_name=args.corpus_name,
                backend_config=rag.RagVectorDbConfig(
                    rag_embedding_model_config=embedding_model_config
                ),
            )
            print(f"  ✅ Created corpus: {rag_corpus.name}")
            print(f"     Display name: {rag_corpus.display_name}")
            corpus_resource_name = rag_corpus.name
        except Exception as e:
            print(f"  ❌ Failed to create corpus: {e}")
            sys.exit(1)
    else:
        corpus_resource_name = existing_corpus.name
        print(f"\n── Step 3: Skipped (corpus already exists)")

    # ── Step 4: Import files from GCS bucket ─────────────────────────────────
    print(f"\n── Step 4: Import files from {bucket}")
    print(f"  Corpus resource: {corpus_resource_name}")
    print(f"  This may take several minutes depending on the number of files...")
    print()

    try:
        transformation_config = rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
            ),
        )

        start_time = time.time()

        import_result = rag.import_files(
            corpus_resource_name,
            [bucket],
            transformation_config=transformation_config,
            max_embedding_requests_per_min=args.embedding_rpm,
        )

        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        print(f"  ✅ Import complete!")
        print(f"     Files imported: {import_result.imported_rag_files_count}")
        print(f"     Time elapsed:   {minutes}m {seconds}s")
    except Exception as e:
        print(f"  ❌ Failed to import files: {e}")
        sys.exit(1)

    # ── Step 5: Verify ───────────────────────────────────────────────────────
    print(f"\n── Step 5: Verify corpus")
    try:
        files = list(rag.list_files(corpus_resource_name))
        print(f"  ✅ Corpus '{args.corpus_name}' has {len(files)} files")
        if files:
            print(f"     First file: {files[0].display_name}")
            if len(files) > 1:
                print(f"     Last file:  {files[-1].display_name}")
    except Exception as e:
        print(f"  ⚠️  Could not verify files: {e}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  Complete")
    print("=" * 60)
    print()
    print(f"  Corpus:    {args.corpus_name}")
    print(f"  Resource:  {corpus_resource_name}")
    print(f"  Bucket:    {bucket}")
    print(f"  Files:     {import_result.imported_rag_files_count}")
    print()
    print("  The corpus will be automatically registered in the database")
    print("  on the next backend startup via CorpusSyncService.")
    print("  Or trigger a manual sync: POST /api/admin/corpora/sync")
    print()
    print("  ✅ Done!")


if __name__ == "__main__":
    main()
