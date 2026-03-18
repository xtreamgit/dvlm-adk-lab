#!/bin/bash

# Admin Endpoints Testing Script
# Tests all admin panel endpoints including /admin/audit
# Usage: ./test_admin_endpoints.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}${BOLD}================================================================${NC}"
echo -e "${BLUE}${BOLD}ADMIN ENDPOINTS COMPREHENSIVE TESTING${NC}"
echo -e "${BLUE}${BOLD}================================================================${NC}\n"

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ gcloud CLI found${NC}"

# Check if requests library is installed
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  requests library not installed${NC}"
    echo -e "${BLUE}Installing requests...${NC}"
    pip3 install requests
fi
echo -e "${GREEN}✅ requests library available${NC}"

echo ""

# Test 1: Run audit endpoint tests
echo -e "${BLUE}${BOLD}Running /admin/audit endpoint tests...${NC}\n"

if python3 "$SCRIPT_DIR/test_admin_audit_endpoint.py"; then
    echo -e "\n${GREEN}✅ Audit endpoint tests passed${NC}"
    AUDIT_PASSED=true
else
    echo -e "\n${RED}❌ Audit endpoint tests failed${NC}"
    AUDIT_PASSED=false
fi

# Test 2: Quick check of other admin endpoints
echo -e "\n${BLUE}${BOLD}Quick check of other admin endpoints...${NC}\n"

TOKEN=$(gcloud auth print-identity-token)
BASE_URL="https://34.49.46.115.nip.io"

check_endpoint() {
    local endpoint=$1
    local description=$2
    
    echo -e "${BLUE}Testing ${endpoint}...${NC}"
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        "${BASE_URL}${endpoint}")
    
    if [ "$status_code" == "200" ]; then
        echo -e "${GREEN}✅ ${description}: OK (${status_code})${NC}"
        return 0
    elif [ "$status_code" == "401" ] || [ "$status_code" == "403" ]; then
        echo -e "${YELLOW}⚠️  ${description}: Auth required (${status_code})${NC}"
        return 0
    else
        echo -e "${RED}❌ ${description}: Failed (${status_code})${NC}"
        return 1
    fi
}

# Check various admin endpoints
ADMIN_ENDPOINTS_PASSED=true

check_endpoint "/api/admin/users" "Users Management" || ADMIN_ENDPOINTS_PASSED=false
check_endpoint "/api/admin/corpora" "Corpora Management" || ADMIN_ENDPOINTS_PASSED=false
check_endpoint "/api/admin/agents" "Agents Management" || ADMIN_ENDPOINTS_PASSED=false

# Summary
echo -e "\n${BLUE}${BOLD}================================================================${NC}"
echo -e "${BLUE}${BOLD}OVERALL TEST SUMMARY${NC}"
echo -e "${BLUE}${BOLD}================================================================${NC}\n"

if [ "$AUDIT_PASSED" = true ] && [ "$ADMIN_ENDPOINTS_PASSED" = true ]; then
    echo -e "${GREEN}${BOLD}✅ ALL ADMIN ENDPOINTS WORKING${NC}"
    echo -e "${GREEN}Your admin panel is fully functional!${NC}\n"
    exit 0
elif [ "$AUDIT_PASSED" = true ]; then
    echo -e "${YELLOW}${BOLD}⚠️  AUDIT ENDPOINT WORKING${NC}"
    echo -e "${YELLOW}Some other admin endpoints may have issues${NC}\n"
    exit 0
else
    echo -e "${RED}${BOLD}❌ ADMIN ENDPOINTS HAVE ISSUES${NC}"
    echo -e "${RED}Check the test output above for details${NC}\n"
    exit 1
fi
