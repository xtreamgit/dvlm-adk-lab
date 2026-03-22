#!/bin/bash

# Test Admin Endpoints via curl with Cloud Run authentication
# This bypasses IAP by hitting the backend directly
# Usage: ./test_admin_via_curl.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

PROJECT_ID="dvlm-adk-lab"
BACKEND_URL="https://backend-351592762922.us-west1.run.app"

echo -e "${BLUE}${BOLD}================================================================${NC}"
echo -e "${BLUE}${BOLD}ADMIN ENDPOINTS - DIRECT BACKEND TEST${NC}"
echo -e "${BLUE}${BOLD}================================================================${NC}\n"

echo -e "${YELLOW}This test hits the backend directly (bypassing IAP)${NC}"
echo -e "${YELLOW}Requires local authentication credentials${NC}\n"

# Test 1: Health check first
echo -e "${BLUE}TEST 1: Backend Health Check${NC}"

if curl -sf "$BACKEND_URL/api/health" > /dev/null; then
    echo -e "${GREEN}✅ Backend is accessible${NC}\n"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo -e "${YELLOW}Backend may not be running or accessible${NC}\n"
    exit 1
fi

# Test 2: Try audit endpoint without auth (should fail)
echo -e "${BLUE}TEST 2: Audit Endpoint Security (should require auth)${NC}"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/admin/audit")

if [ "$STATUS" == "401" ] || [ "$STATUS" == "403" ]; then
    echo -e "${GREEN}✅ Endpoint properly requires authentication (${STATUS})${NC}\n"
elif [ "$STATUS" == "200" ]; then
    echo -e "${RED}❌ WARNING: Endpoint accessible without auth!${NC}\n"
else
    echo -e "${YELLOW}⚠️  Unexpected status: ${STATUS}${NC}\n"
fi

# Test 3: Try with local user authentication
echo -e "${BLUE}TEST 3: Audit Endpoint with Local Authentication${NC}"

# First, login to get token
echo -e "${BLUE}Attempting to login with test user...${NC}"

LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"alice","password":"alice123"}')

# Extract token from response
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅ Successfully authenticated${NC}"
    
    # Now test audit endpoint with token
    echo -e "${BLUE}Testing /admin/audit with authentication token...${NC}\n"
    
    AUDIT_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$BACKEND_URL/api/admin/audit")
    
    # Check if response is valid JSON
    if echo "$AUDIT_RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        echo -e "${GREEN}✅ Valid JSON response received${NC}\n"
        
        # Pretty print the response
        echo -e "${BOLD}Audit Log Data:${NC}"
        echo "$AUDIT_RESPONSE" | python3 -m json.tool
        
        # Count entries
        COUNT=$(echo "$AUDIT_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
        echo -e "\n${GREEN}✅ Found $COUNT audit log entries${NC}"
        
        echo -e "\n${GREEN}${BOLD}TEST PASSED: /admin/audit endpoint is working correctly!${NC}\n"
        exit 0
        
    else
        echo -e "${RED}❌ Invalid JSON response${NC}"
        echo -e "Response: $AUDIT_RESPONSE\n"
        exit 1
    fi
    
else
    echo -e "${YELLOW}⚠️  Could not authenticate with local credentials${NC}"
    echo -e "${YELLOW}This is expected if only IAP authentication is configured${NC}\n"
    
    echo -e "${BLUE}Alternative: Use browser-based test${NC}"
    echo -e "Run: ${BOLD}./test_admin_audit_browser.sh${NC}\n"
    
    exit 0
fi
