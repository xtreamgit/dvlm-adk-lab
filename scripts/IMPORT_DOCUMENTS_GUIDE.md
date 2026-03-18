# Import Documents via Vertex AI Agent Builder UI

## Step-by-Step Guide

### 1. Open Vertex AI Agent Builder

Click this link to go directly to your search engine:
**https://console.cloud.google.com/gen-app-builder/engines/default-corpus-datastore-engine/data?project=dvlm-adk-lab**

Or navigate manually:
1. Go to: https://console.cloud.google.com/gen-app-builder
2. Select project: `dvlm-adk-lab`
3. Click on `default-corpus-datastore-engine`

### 2. Import Documents

Once in the search engine dashboard:

1. **Click on the "Data" tab** (should be selected by default)

2. **Click "IMPORT" button** (top right)

3. **Select import source:**
   - Choose: **"Cloud Storage"**
   - Click "Continue"

4. **Configure import settings:**
   
   **Import from Cloud Storage:**
   - **Bucket**: `adk-rag-default-corpus-bucket-dvlm-adk-lab`
   - **Folder/File pattern**: `documents/*.pdf` or `documents/`
   - **File type**: Select "PDF" or "Unstructured documents"
   
   **Advanced options (optional):**
   - **Chunking**: Leave as default (Auto)
   - **Metadata**: None needed for now
   
5. **Click "IMPORT"**

### 3. Monitor Import Progress

After clicking import:

1. You'll see an import operation start
2. Status will show as "In progress"
3. **Import time**: 10-30 minutes for 70 PDFs (~700 MB)

You can monitor progress:
- Refresh the page to see updated status
- Check "Import history" tab for details
- Look for "Documents" count to increase

### 4. Verify Import Completion

Once import completes:

✅ **Documents tab** should show ~70 documents
✅ **Status** should be "Active" or "Ready"
✅ **Last import** should show recent timestamp

### 5. Test Search (Optional)

In the Agent Builder UI:

1. Click on "Preview" tab
2. Enter a test query like: "What is machine learning?"
3. You should see:
   - Document snippets
   - LLM-generated summary
   - Source citations

## Troubleshooting

### "No files found"
- Check bucket name: `adk-rag-default-corpus-bucket-dvlm-adk-lab`
- Verify folder path: `documents/`
- Ensure PDFs are in the bucket: `gsutil ls gs://adk-rag-default-corpus-bucket-dvlm-adk-lab/documents/`

### "Import failed"
- Check file formats (should be PDF)
- Verify file sizes (some very large PDFs may fail)
- Check error logs in import history

### "Taking too long"
- Normal for 70 PDFs
- Can take 15-30 minutes
- Check back periodically

## Alternative: Import via gcloud CLI

If you prefer command line:

```bash
# This requires the data to be in JSONL format
# For PDFs, the UI method is recommended
```

## After Import Completes

Once documents are imported:

1. ✅ Return to this terminal
2. ✅ Test queries via the frontend application
3. ✅ Verify RAG responses include document content
4. ✅ Continue with Phase 7 (Model Armor integration)

## Quick Verification Command

After import, test via API:

```bash
# Start the backend server
cd backend
source .venv/bin/activate
python -m uvicorn src.main:app --reload

# In another terminal, test query
curl -X POST http://localhost:8080/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "83c93fdd-e887-4938-9ed4-65ba79f503a3",
    "tool_name": "rag_query",
    "corpus_id": "ada80efa-0d46-4e80-8f8a-17647eafa311",
    "query": "What is machine learning?"
  }'
```

Expected response should include:
- Document snippets from your PDFs
- LLM summary
- Citations

## Current Configuration

- **Project**: dvlm-adk-lab
- **Data Store**: default-corpus-datastore
- **Search Engine**: default-corpus-datastore-engine
- **GCS Bucket**: adk-rag-default-corpus-bucket-dvlm-adk-lab
- **Documents**: 70 PDFs in `documents/` folder
- **Total Size**: ~700 MB

## Next Steps

After successful import:

1. Test queries through frontend UI
2. Verify search quality and relevance
3. Proceed to Phase 7: Model Armor integration
4. Configure IAP authentication
5. Deploy to production
