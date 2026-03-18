# Vertex AI Search & Conversation Setup Guide

## Overview

This guide explains how to set up Vertex AI Search & Conversation (the replacement for the deprecated Vertex AI RAG API) to enable document querying in the ADK RAG application.

## What Changed

- **Old**: Vertex AI RAG API (deprecated/unavailable)
- **New**: Vertex AI Search & Conversation API
- **Benefits**: 
  - More mature and stable API
  - Better search quality with LLM-powered summaries
  - Built-in spell correction and query expansion
  - Extractive answers and snippets

## Prerequisites

### 1. Enable Vertex AI Search API

```bash
gcloud services enable discoveryengine.googleapis.com
```

### 2. Install Required Package

Already installed in your virtual environment:
```bash
pip install google-cloud-discoveryengine
```

### 3. Verify GCS Bucket and Documents

The setup script already created the bucket and uploaded documents:
```bash
gsutil ls gs://adk-rag-default-corpus-bucket-dvlm-adk-lab/documents/
```

You should see 70 PDF files.

## Running the Setup

### Step 1: Set Environment Variables

```bash
export GCP_PROJECT_ID="dvlm-adk-lab"
```

### Step 2: Run the Setup Script

```bash
GCP_PROJECT_ID="dvlm-adk-lab" .venv/bin/python3 scripts/create_vertex_search_datastore.py
```

This script will:
1. ✅ Create a Vertex AI Search data store
2. ✅ Import all 70 PDFs from GCS
3. ✅ Create a search engine with LLM add-on
4. ✅ Update the database with the data store ID

**Note**: Document import can take 10-30 minutes depending on the number and size of documents.

## What Gets Created

### Data Store
- **Name**: `default-corpus-datastore`
- **Type**: Unstructured data (PDFs)
- **Location**: Global
- **Content**: 70 PDF documents (~700 MB)

### Search Engine
- **Name**: `default-corpus-datastore-engine`
- **Features**:
  - Standard search tier
  - LLM-powered summaries
  - Query expansion
  - Spell correction
  - Extractive answers

## Verification

### Check Data Store Status

```bash
gcloud alpha discovery-engine data-stores list \
  --location=global \
  --collection=default_collection \
  --project=dvlm-adk-lab
```

### Check Document Import Status

Via Google Cloud Console:
1. Go to: https://console.cloud.google.com/gen-app-builder/engines
2. Select your project: `dvlm-adk-lab`
3. Click on `default-corpus-datastore-engine`
4. Check "Data" tab for import status

### Test Query via API

Once import is complete, test a query:

```bash
curl -X POST http://localhost:8080/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "83c93fdd-e887-4938-9ed4-65ba79f503a3",
    "tool_name": "rag_query",
    "corpus_id": "ada80efa-0d46-4e80-8f8a-17647eafa311",
    "query": "What is machine learning?"
  }'
```

Expected response:
- Results with document snippets
- LLM-generated summary
- Citations and sources

## Backend Changes

The backend has been updated to use Vertex AI Search:

### Updated Files

1. **`backend/src/services/vertex_rag_service.py`**
   - Replaced `google.cloud.aiplatform.rag` with `google.cloud.discoveryengine_v1`
   - Updated `query_corpus()` to use Search API
   - Added support for:
     - Query expansion
     - Spell correction
     - Extractive answers
     - LLM summaries

2. **`backend/requirements.txt`** (needs update)
   - Add: `google-cloud-discoveryengine>=0.17.0`

## Troubleshooting

### "API not enabled"

Enable the Discovery Engine API:
```bash
gcloud services enable discoveryengine.googleapis.com --project=dvlm-adk-lab
```

### "Permission denied"

Ensure your service account has:
- `discoveryengine.dataStores.create`
- `discoveryengine.documents.import`
- `discoveryengine.engines.create`

### "Import taking too long"

Document import is asynchronous and can take time:
- Small datasets (< 100 docs): 5-10 minutes
- Medium datasets (100-1000 docs): 10-30 minutes
- Large datasets (> 1000 docs): 30+ minutes

Check status in Cloud Console or via API.

### "No results returned"

Wait for import to complete. The search engine won't return results until documents are fully indexed.

## Cost Considerations

Vertex AI Search pricing:
- **Data storage**: ~$0.30 per GB per month
- **Queries**: ~$0.002 per query
- **LLM summaries**: Additional cost per summary

For 700 MB of documents with moderate usage:
- Storage: ~$0.21/month
- 1000 queries/month: ~$2.00
- Total: ~$2-5/month

## Next Steps

After setup is complete:

1. ✅ Test queries via frontend
2. ✅ Verify search quality
3. ⏭️ Integrate Model Armor (Phase 7)
4. ⏭️ Configure IAP (Phase 8)
5. ⏭️ Deploy to production (Phase 9)

## Resources

- [Vertex AI Search Documentation](https://cloud.google.com/generative-ai-app-builder/docs/introduction)
- [Search API Reference](https://cloud.google.com/generative-ai-app-builder/docs/reference/rest)
- [Pricing](https://cloud.google.com/generative-ai-app-builder/pricing)
