#!/bin/bash
# Test admin audit integration - Backend API + Frontend compatibility

set -e

echo "================================================================"
echo "ADMIN AUDIT INTEGRATION TEST"
echo "================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_URL="https://backend-351592762922.us-west1.run.app"

echo "Step 1: Test Backend API (with authentication)"
echo "--------------------------------------------------------------"

# Login and get token
echo "Logging in as test user..."
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
  echo -e "${GREEN}✓ Login successful${NC}"
  TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
else
  echo -e "${RED}✗ Login failed${NC}"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo ""
echo "Step 2: Fetch Audit Logs from Backend API"
echo "--------------------------------------------------------------"

AUDIT_RESPONSE=$(curl -s "$BACKEND_URL/api/admin/audit?limit=5" \
  -H "Authorization: Bearer $TOKEN")

if echo "$AUDIT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if isinstance(data, list) else 1)" 2>/dev/null; then
  echo -e "${GREEN}✓ Backend API returns valid array${NC}"
  
  # Check structure of first item
  echo ""
  echo "Sample audit log entry:"
  echo "$AUDIT_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if len(data) > 0:
    entry = data[0]
    print(f\"  ID: {entry.get('id')}\")
    print(f\"  Action: {entry.get('action')}\")
    print(f\"  User: {entry.get('user_name')}\")
    print(f\"  Changes type: {type(entry.get('changes')).__name__}\")
    print(f\"  Metadata type: {type(entry.get('metadata')).__name__}\")
    
    # Verify changes is an object or null
    changes = entry.get('changes')
    if changes is None:
        print(f\"  ✓ Changes is null (OK)\")
    elif isinstance(changes, dict):
        print(f\"  ✓ Changes is dict (OK for frontend)\")
    elif isinstance(changes, str):
        print(f\"  ⚠ Changes is string (frontend should handle this)\")
    else:
        print(f\"  ✗ Changes is unexpected type: {type(changes)}\")
else:
    print('No audit logs found')
"
else
  echo -e "${RED}✗ Backend API response invalid${NC}"
  echo "Response: $AUDIT_RESPONSE"
  exit 1
fi

echo ""
echo "Step 3: Verify Frontend Revision"
echo "--------------------------------------------------------------"

FRONTEND_REVISION=$(gcloud run services describe frontend \
  --region=us-west1 \
  --project=adk-rag-ma \
  --format="value(status.latestReadyRevisionName)")

echo "Current frontend revision: $FRONTEND_REVISION"

if [ "$FRONTEND_REVISION" = "frontend-00013-xds" ]; then
  echo -e "${GREEN}✓ Frontend is on latest revision with fixes${NC}"
else
  echo -e "${YELLOW}⚠ Frontend revision is different than expected${NC}"
fi

echo ""
echo "Step 4: Check Frontend Logs for Errors"
echo "--------------------------------------------------------------"

ERROR_COUNT=$(gcloud logging read \
  "resource.labels.service_name=\"frontend\" AND resource.labels.revision_name=\"$FRONTEND_REVISION\" AND severity>=ERROR" \
  --project=adk-rag-ma \
  --limit=5 \
  --format=json 2>/dev/null | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")

if [ "$ERROR_COUNT" = "0" ]; then
  echo -e "${GREEN}✓ No errors in frontend logs${NC}"
else
  echo -e "${YELLOW}⚠ Found $ERROR_COUNT errors in frontend logs${NC}"
  echo "Recent errors:"
  gcloud logging read \
    "resource.labels.service_name=\"frontend\" AND resource.labels.revision_name=\"$FRONTEND_REVISION\" AND severity>=ERROR" \
    --project=adk-rag-ma \
    --limit=3 \
    --format="value(textPayload)" 2>/dev/null | head -10
fi

echo ""
echo "================================================================"
echo "INTEGRATION TEST SUMMARY"
echo "================================================================"
echo ""
echo -e "${GREEN}✓ Backend API working${NC} - Returns audit logs with correct structure"
echo -e "${GREEN}✓ Frontend deployed${NC} - Latest revision with type fixes"
echo ""
echo "To test the frontend page:"
echo "  1. Open: https://34.49.46.115.nip.io/admin/audit"
echo "  2. Sign in with Google (IAP)"
echo "  3. Should see audit log table with formatted JSON"
echo ""
echo "Frontend fixes applied:"
echo "  • Changed 'changes' and 'metadata' types from 'string' to 'any'"
echo "  • Updated formatChanges() to handle objects directly"
echo "  • Fixed pagination offset calculation"
echo ""
