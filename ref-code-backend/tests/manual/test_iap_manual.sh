#!/bin/bash
#
# Manual IAP Integration Testing Script
# Tests IAP endpoints and configuration
#

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8080}"
IAP_JWT="${IAP_JWT:-test.jwt.token}"
VERBOSE="${VERBOSE:-false}"

echo "=========================================="
echo "IAP Integration Manual Test Suite"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo ""

# Test counter
PASSED=0
FAILED=0

# Test helper function
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"
    local headers="$5"
    
    echo -n "Testing: $name ... "
    
    if [ "$VERBOSE" = "true" ]; then
        echo ""
        echo "  Method: $method"
        echo "  Endpoint: $endpoint"
        echo "  Expected: $expected_status"
    fi
    
    # Make request
    if [ -n "$headers" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" $headers)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint")
    fi
    
    # Extract status code (last line)
    status=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$VERBOSE" = "true" ]; then
        echo "  Response Status: $status"
        echo "  Response Body: $body"
    fi
    
    # Check status code
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: $expected_status, Got: $status)"
        if [ "$VERBOSE" != "true" ]; then
            echo "  Response: $body"
        fi
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "1. Testing IAP Status Endpoint"
echo "--------------------------------"
test_endpoint \
    "Check IAP configuration status" \
    "GET" \
    "/api/iap/status" \
    "200" \
    ""

echo ""
echo "2. Testing IAP Headers Endpoint (No IAP)"
echo "-----------------------------------------"
test_endpoint \
    "Get IAP headers without authentication" \
    "GET" \
    "/api/iap/headers" \
    "200" \
    ""

echo ""
echo "3. Testing IAP Verify Endpoint (Missing Header)"
echo "------------------------------------------------"
test_endpoint \
    "Verify IAP token without JWT header" \
    "GET" \
    "/api/iap/verify" \
    "401" \
    ""

echo ""
echo "4. Testing IAP Me Endpoint (Missing Header)"
echo "--------------------------------------------"
test_endpoint \
    "Get current user without IAP authentication" \
    "GET" \
    "/api/iap/me" \
    "401" \
    ""

echo ""
echo "5. Testing Health Check"
echo "-----------------------"
test_endpoint \
    "Application health check" \
    "GET" \
    "/api/health" \
    "200" \
    ""

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
