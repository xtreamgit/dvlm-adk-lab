#!/bin/bash
# Test document retrieval with hector credentials
set -e

BACKEND_URL="https://backend-351592762922.us-west1.run.app"

echo "Testing Document Download Functionality"
echo "========================================================================"
echo ""

# Step 1: Login with hector/hector123
echo "Step 1: Logging in as hector..."
LOGIN_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "hector",
    "password": "hector123"
  }')

echo "Login response:"
echo "$LOGIN_RESPONSE" | jq '.'

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed - no access_token received"
  exit 1
fi

echo "✅ Login successful - token received"
echo ""

# Step 2: Get list of corpora
echo "Step 2: Getting list of corpora..."
CORPORA_RESPONSE=$(curl -s -X GET "${BACKEND_URL}/api/corpora/" \
  -H "Authorization: Bearer $TOKEN")

echo "Corpora response:"
echo "$CORPORA_RESPONSE" | jq '.'

# Check if response is an array and has elements
CORPUS_COUNT=$(echo "$CORPORA_RESPONSE" | jq '. | length')
echo "Corpus count: $CORPUS_COUNT"

if [ "$CORPUS_COUNT" == "0" ] || [ "$CORPUS_COUNT" == "null" ]; then
  echo "❌ No corpora found or access denied"
  echo "Full response: $CORPORA_RESPONSE"
  exit 1
fi

CORPUS_ID=$(echo "$CORPORA_RESPONSE" | jq -r '.[0].id')
CORPUS_NAME=$(echo "$CORPORA_RESPONSE" | jq -r '.[0].name')

if [ "$CORPUS_ID" == "null" ] || [ -z "$CORPUS_ID" ]; then
  echo "❌ Could not extract corpus ID"
  exit 1
fi

echo "✅ Found corpus: $CORPUS_NAME (ID: $CORPUS_ID)"
echo ""

# Step 3: List documents in corpus
echo "Step 3: Listing documents in corpus..."
DOCS_RESPONSE=$(curl -s -X GET "${BACKEND_URL}/api/documents/corpus/${CORPUS_ID}/list" \
  -H "Authorization: Bearer $TOKEN")

echo "Documents response:"
echo "$DOCS_RESPONSE" | jq '.'

DOCUMENT_NAME=$(echo "$DOCS_RESPONSE" | jq -r '.documents[0].display_name')

if [ "$DOCUMENT_NAME" == "null" ] || [ -z "$DOCUMENT_NAME" ]; then
  echo "❌ No documents found in corpus"
  exit 1
fi

echo "✅ Found document: $DOCUMENT_NAME"
echo ""

# Step 4: Retrieve document and generate signed URL
echo "Step 4: Retrieving document '$DOCUMENT_NAME'..."
RETRIEVE_RESPONSE=$(curl -s -X GET "${BACKEND_URL}/api/documents/retrieve?corpus_id=${CORPUS_ID}&document_name=${DOCUMENT_NAME}&generate_url=true" \
  -H "Authorization: Bearer $TOKEN")

echo "Retrieve response:"
echo "$RETRIEVE_RESPONSE" | jq '.'

SIGNED_URL=$(echo "$RETRIEVE_RESPONSE" | jq -r '.access.url')
EXPIRES_AT=$(echo "$RETRIEVE_RESPONSE" | jq -r '.access.expires_at')

if [ "$SIGNED_URL" == "null" ] || [ -z "$SIGNED_URL" ]; then
  echo "❌ Failed to generate signed URL"
  echo "Response: $RETRIEVE_RESPONSE"
  exit 1
fi

echo "✅ Signed URL generated successfully!"
echo ""

# Step 5: Test the signed URL
echo "Step 5: Testing signed URL..."
echo "URL: ${SIGNED_URL:0:80}..."
echo "Expires: $EXPIRES_AT"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -I "$SIGNED_URL")

if [ "$HTTP_CODE" == "200" ]; then
  echo "✅ Signed URL is valid and accessible (HTTP $HTTP_CODE)"
else
  echo "❌ Signed URL returned HTTP $HTTP_CODE"
  exit 1
fi

echo ""
echo "========================================================================"
echo "✅ ALL TESTS PASSED!"
echo "Document download functionality is working correctly."
echo "========================================================================"
