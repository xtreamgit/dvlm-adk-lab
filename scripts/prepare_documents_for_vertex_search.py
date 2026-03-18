#!/usr/bin/env python3
"""
Prepare PDF documents for Vertex AI Search by creating JSONL metadata files.

Vertex AI Search requires documents to be in JSONL format with metadata.
This script creates the necessary metadata files for our PDFs.
"""

import os
import json
from pathlib import Path
from google.cloud import storage

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "dvlm-adk-lab")
BUCKET_NAME = "adk-rag-default-corpus-bucket-dvlm-adk-lab"
DATA_DIR = Path(__file__).parent.parent / "data"


def create_document_metadata():
    """Create JSONL metadata file for all PDFs."""
    print(f"\n📝 Creating document metadata for Vertex AI Search")
    
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    
    # List all PDFs in the bucket
    blobs = list(bucket.list_blobs(prefix="documents/"))
    pdf_blobs = [b for b in blobs if b.name.endswith('.pdf')]
    
    print(f"Found {len(pdf_blobs)} PDF files in bucket")
    
    # Create metadata entries
    metadata_entries = []
    for blob in pdf_blobs:
        # Extract filename without extension for title
        filename = blob.name.split('/')[-1]
        title = filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ')
        
        # Create metadata entry
        entry = {
            "id": blob.name.replace('documents/', '').replace('.pdf', '').replace(' ', '-').lower(),
            "structData": {
                "title": title,
                "uri": f"gs://{BUCKET_NAME}/{blob.name}",
                "mimeType": "application/pdf"
            },
            "content": {
                "mimeType": "application/pdf",
                "uri": f"gs://{BUCKET_NAME}/{blob.name}"
            }
        }
        metadata_entries.append(entry)
    
    # Write to JSONL file
    metadata_file = "/tmp/documents_metadata.jsonl"
    with open(metadata_file, 'w') as f:
        for entry in metadata_entries:
            f.write(json.dumps(entry) + '\n')
    
    print(f"✅ Created metadata file: {metadata_file}")
    print(f"   Entries: {len(metadata_entries)}")
    
    # Upload metadata file to GCS
    metadata_blob = bucket.blob("metadata/documents_metadata.jsonl")
    metadata_blob.upload_from_filename(metadata_file)
    
    metadata_uri = f"gs://{BUCKET_NAME}/metadata/documents_metadata.jsonl"
    print(f"✅ Uploaded metadata to: {metadata_uri}")
    
    return metadata_uri


def main():
    """Main function."""
    print("=" * 80)
    print("Prepare Documents for Vertex AI Search")
    print("=" * 80)
    
    try:
        metadata_uri = create_document_metadata()
        
        print("\n" + "=" * 80)
        print("✅ Preparation Complete!")
        print("=" * 80)
        print(f"\nMetadata URI: {metadata_uri}")
        print("\nNext step: Update the import script to use this metadata file")
        print("Or manually import via Cloud Console using this JSONL file")
        
    except Exception as e:
        print(f"\n❌ Preparation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
