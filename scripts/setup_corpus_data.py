#!/usr/bin/env python3
"""
Setup script to create GCS bucket, Vertex AI RAG corpus, and upload documents.

This script:
1. Creates a GCS bucket for the default corpus
2. Creates a Vertex AI RAG corpus
3. Uploads all PDFs from the /data directory to the bucket
4. Imports the documents into the Vertex AI RAG corpus
5. Updates the database with the corpus information

Prerequisites:
- Google Cloud SDK installed and authenticated
- GOOGLE_APPLICATION_CREDENTIALS environment variable set
- Required Python packages: google-cloud-storage, google-cloud-aiplatform
"""

import os
import sys
import asyncio
import asyncpg
from pathlib import Path
from google.cloud import storage
from google.cloud import aiplatform
from datetime import datetime

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
BUCKET_NAME = "adk-rag-default-corpus-bucket-dvlm-adk-lab"
CORPUS_NAME = "default-corpus"
DATA_DIR = Path(__file__).parent.parent / "data"

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "adk_rag_production")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def create_gcs_bucket(bucket_name: str, project_id: str, location: str):
    """Create a GCS bucket if it doesn't exist."""
    print(f"\n📦 Creating GCS bucket: {bucket_name}")
    
    storage_client = storage.Client(project=project_id)
    
    # Check if bucket exists
    bucket = storage_client.bucket(bucket_name)
    if bucket.exists():
        print(f"✅ Bucket {bucket_name} already exists")
        return bucket
    
    # Create bucket
    bucket = storage_client.create_bucket(
        bucket_name,
        location=location,
        project=project_id
    )
    print(f"✅ Created bucket {bucket_name} in {location}")
    return bucket


def upload_pdfs_to_gcs(bucket_name: str, data_dir: Path):
    """Upload all PDF files from data directory to GCS bucket."""
    print(f"\n📤 Uploading PDFs from {data_dir} to {bucket_name}")
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    pdf_files = list(data_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files")
    
    uploaded_files = []
    for pdf_file in pdf_files:
        blob_name = f"documents/{pdf_file.name}"
        blob = bucket.blob(blob_name)
        
        if blob.exists():
            print(f"  ⏭️  Skipping {pdf_file.name} (already exists)")
        else:
            print(f"  ⬆️  Uploading {pdf_file.name} ({pdf_file.stat().st_size / 1024 / 1024:.2f} MB)")
            blob.upload_from_filename(str(pdf_file))
        
        uploaded_files.append(f"gs://{bucket_name}/{blob_name}")
    
    print(f"✅ Uploaded {len(uploaded_files)} files to GCS")
    return uploaded_files


def create_vertex_rag_corpus(corpus_name: str, project_id: str, location: str):
    """Create a Vertex AI RAG corpus."""
    print(f"\n🧠 Creating Vertex AI RAG corpus: {corpus_name}")
    
    aiplatform.init(project=project_id, location=location)
    
    try:
        # Create RAG corpus
        from google.cloud.aiplatform import rag
        
        corpus = rag.create_corpus(
            display_name=corpus_name,
            description="Default corpus with sample documents for ADK RAG application"
        )
        
        corpus_id = corpus.name
        print(f"✅ Created Vertex AI RAG corpus: {corpus_id}")
        return corpus_id
        
    except Exception as e:
        print(f"❌ Error creating Vertex AI RAG corpus: {e}")
        print("Note: Vertex AI RAG API might not be available in your project/region")
        return None


def import_files_to_rag_corpus(corpus_id: str, file_uris: list, project_id: str, location: str):
    """Import files into Vertex AI RAG corpus."""
    print(f"\n📥 Importing {len(file_uris)} files into RAG corpus")
    
    aiplatform.init(project=project_id, location=location)
    
    try:
        from google.cloud.aiplatform import rag
        
        # Import files in batches (Vertex AI has limits)
        batch_size = 10
        for i in range(0, len(file_uris), batch_size):
            batch = file_uris[i:i + batch_size]
            print(f"  Importing batch {i // batch_size + 1} ({len(batch)} files)")
            
            rag.import_files(
                corpus_name=corpus_id,
                paths=batch,
                chunk_size=512,
                chunk_overlap=100
            )
        
        print(f"✅ Imported all files into RAG corpus")
        
    except Exception as e:
        print(f"❌ Error importing files: {e}")


async def update_database(corpus_id: str, vertex_rag_corpus_id: str):
    """Update the database with the Vertex AI RAG corpus ID."""
    print(f"\n💾 Updating database with corpus information")
    
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    try:
        await conn.execute(
            """
            UPDATE corpora 
            SET vertex_rag_corpus_id = $1, updated_at = $2
            WHERE corpus_name = $3
            """,
            vertex_rag_corpus_id,
            datetime.utcnow(),
            CORPUS_NAME
        )
        print(f"✅ Updated database with Vertex AI RAG corpus ID")
        
    finally:
        await conn.close()


async def main():
    """Main setup function."""
    print("=" * 80)
    print("ADK RAG Corpus Setup Script")
    print("=" * 80)
    
    # Validate configuration
    if PROJECT_ID == "your-project-id":
        print("\n❌ Error: Please set GCP_PROJECT_ID environment variable")
        print("   export GCP_PROJECT_ID=your-google-cloud-project-id")
        sys.exit(1)
    
    if not DATA_DIR.exists():
        print(f"\n❌ Error: Data directory not found: {DATA_DIR}")
        sys.exit(1)
    
    print(f"\nConfiguration:")
    print(f"  Project ID: {PROJECT_ID}")
    print(f"  Location: {LOCATION}")
    print(f"  Bucket: {BUCKET_NAME}")
    print(f"  Corpus: {CORPUS_NAME}")
    print(f"  Data Directory: {DATA_DIR}")
    
    try:
        # Step 1: Create GCS bucket
        bucket = create_gcs_bucket(BUCKET_NAME, PROJECT_ID, LOCATION)
        
        # Step 2: Upload PDFs to GCS
        uploaded_files = upload_pdfs_to_gcs(BUCKET_NAME, DATA_DIR)
        
        # Step 3: Create Vertex AI RAG corpus
        vertex_corpus_id = create_vertex_rag_corpus(CORPUS_NAME, PROJECT_ID, LOCATION)
        
        if vertex_corpus_id:
            # Step 4: Import files into RAG corpus
            import_files_to_rag_corpus(vertex_corpus_id, uploaded_files, PROJECT_ID, LOCATION)
            
            # Step 5: Update database
            corpus_db_id = "ada80efa-0d46-4e80-8f8a-17647eafa311"  # From seed data
            await update_database(corpus_db_id, vertex_corpus_id)
        else:
            print("\n⚠️  Vertex AI RAG corpus creation failed")
            print("Files are uploaded to GCS but not indexed in Vertex AI RAG")
        
        print("\n" + "=" * 80)
        print("✅ Setup Complete!")
        print("=" * 80)
        print(f"\nBucket: gs://{BUCKET_NAME}")
        print(f"Documents uploaded: {len(uploaded_files)}")
        if vertex_corpus_id:
            print(f"Vertex AI RAG Corpus: {vertex_corpus_id}")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
