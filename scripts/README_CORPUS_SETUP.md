# Corpus Data Setup Guide

## Overview

The default corpus needs to be populated with the PDF documents from the `/data` directory. This requires:
1. A Google Cloud Storage (GCS) bucket
2. A Vertex AI RAG corpus
3. Uploading and indexing the documents

## Current Status

- ✅ Database corpus entry exists (`default-corpus`)
- ✅ 70+ PDF files available in `/data` directory
- ❌ GCS bucket not created yet
- ❌ Vertex AI RAG corpus not created yet
- ❌ Documents not uploaded/indexed

## Prerequisites

### 1. Google Cloud Project Setup

```bash
# Set your Google Cloud project ID
export GCP_PROJECT_ID="your-project-id"
export GCP_LOCATION="us-central1"

# Authenticate with Google Cloud
gcloud auth application-default login

# Enable required APIs
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

### 2. Install Required Python Packages

```bash
cd backend
source .venv/bin/activate
pip install google-cloud-storage google-cloud-aiplatform
```

### 3. Set Database Credentials

```bash
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="adk_rag_production"
export DB_USER="postgres"
export DB_PASSWORD=""  # Set if needed
```

## Running the Setup Script

### Option 1: Automated Setup (Recommended)

```bash
# Make the script executable
chmod +x scripts/setup_corpus_data.py

# Run the setup script
python3 scripts/setup_corpus_data.py
```

This script will:
1. Create the GCS bucket `adk-rag-default-corpus-bucket-dvlm-adk-lab`
2. Upload all 70+ PDFs from `/data` to the bucket
3. Create a Vertex AI RAG corpus
4. Import and index all documents
5. Update the database with the corpus ID

### Option 2: Manual Setup

#### Step 1: Create GCS Bucket

```bash
gsutil mb -p $GCP_PROJECT_ID -l $GCP_LOCATION gs://adk-rag-default-corpus-bucket-dvlm-adk-lab
```

#### Step 2: Upload PDFs

```bash
gsutil -m cp data/*.pdf gs://adk-rag-default-corpus-bucket-dvlm-adk-lab/documents/
```

#### Step 3: Create Vertex AI RAG Corpus

Use the Google Cloud Console or API to create a RAG corpus and import the documents.

#### Step 4: Update Database

```sql
UPDATE corpora 
SET vertex_rag_corpus_id = 'your-vertex-corpus-id'
WHERE corpus_name = 'default-corpus';
```

## Verification

After setup, verify the corpus is working:

```bash
# Check bucket contents
gsutil ls gs://adk-rag-default-corpus-bucket-dvlm-adk-lab/documents/

# Check database
psql -d adk_rag_production -c "SELECT corpus_name, vertex_rag_corpus_id, gcs_bucket FROM corpora;"

# Test query via API
curl -X POST http://localhost:8080/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "83c93fdd-e887-4938-9ed4-65ba79f503a3",
    "tool_name": "rag_query",
    "corpus_id": "ada80efa-0d46-4e80-8f8a-17647eafa311",
    "query": "What is machine learning?"
  }'
```

## Troubleshooting

### "Vertex AI RAG API not available"

Vertex AI RAG might not be available in all regions. Try:
- Using `us-central1` region
- Checking if the API is enabled in your project
- Verifying your project has the necessary quotas

### "Permission denied"

Ensure your service account has:
- `storage.buckets.create`
- `storage.objects.create`
- `aiplatform.ragCorpora.create`
- `aiplatform.ragFiles.import`

### "Files not uploading"

Check:
- File sizes (some PDFs are large, may take time)
- Network connectivity
- GCS quotas

## Alternative: Local Development Mode

For local development without Google Cloud:

1. Use a mock RAG service that searches local files
2. Implement a simple text search over PDFs
3. Use the documents for testing UI/UX without actual RAG

See `backend/src/services/vertex_rag_service.py` for implementation options.

## Document Statistics

Total PDFs: 70+
Total Size: ~700 MB
Topics: AI, Machine Learning, Programming, Cloud, Security, Data Science

Sample documents:
- artificial-intelligence-a-modern-approach.pdf
- understanding-deep-learning.pdf
- security_concepts.pdf
- cloud-computing.pdf
- python-data-analytics-with-pandas-numpy-and-matplotlib.pdf
