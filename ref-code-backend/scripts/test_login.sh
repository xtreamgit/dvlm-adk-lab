#!/bin/bash

# Login Testing Script
# Tests authentication and authorization for different users

BASE_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Testing User Login & RBAC"
echo "=========================================="
echo ""

# Test 1: Admin Login
echo -e "${BLUE}Test 1: Admin Login${NC}"
ADMIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}')

ADMIN_TOKEN=$(echo $ADMIN_RESPONSE | jq -r '.access_token')
if [ "$ADMIN_TOKEN" != "null" ] && [ -n "$ADMIN_TOKEN" ]; then
    echo -e "${GREEN}✓ Admin login successful${NC}"
    ADMIN_USER=$(echo $ADMIN_RESPONSE | jq -r '.user.username')
    echo "  Username: $ADMIN_USER"
else
    echo -e "${RED}✗ Admin login failed${NC}"
    echo "  Response: $(echo $ADMIN_RESPONSE | jq -r '.detail')"
fi
echo ""

# Test 2: Alice Login (Developer)
echo -e "${BLUE}Test 2: Alice Login (Developer)${NC}"
ALICE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}')

ALICE_TOKEN=$(echo $ALICE_RESPONSE | jq -r '.access_token')
if [ "$ALICE_TOKEN" != "null" ] && [ -n "$ALICE_TOKEN" ]; then
    echo -e "${GREEN}✓ Alice login successful${NC}"
    ALICE_EMAIL=$(echo $ALICE_RESPONSE | jq -r '.user.email')
    echo "  Email: $ALICE_EMAIL"
    
    # Check Alice's corpora
    ALICE_CORPORA=$(curl -s -X GET "$BASE_URL/api/corpora/" \
      -H "Authorization: Bearer $ALICE_TOKEN")
    ALICE_COUNT=$(echo $ALICE_CORPORA | jq '. | length')
    echo "  Corpora accessible: $ALICE_COUNT"
    echo $ALICE_CORPORA | jq '.[] | "    - \(.name) (\(.permission) access)"'
else
    echo -e "${RED}✗ Alice login failed${NC}"
fi
echo ""

# Test 3: Bob Login (Manager)
echo -e "${BLUE}Test 3: Bob Login (Manager)${NC}"
BOB_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","password":"bob12345"}')

BOB_TOKEN=$(echo $BOB_RESPONSE | jq -r '.access_token')
if [ "$BOB_TOKEN" != "null" ] && [ -n "$BOB_TOKEN" ]; then
    echo -e "${GREEN}✓ Bob login successful${NC}"
    
    BOB_CORPORA=$(curl -s -X GET "$BASE_URL/api/corpora/" \
      -H "Authorization: Bearer $BOB_TOKEN")
    BOB_COUNT=$(echo $BOB_CORPORA | jq '. | length')
    echo "  Corpora accessible: $BOB_COUNT"
else
    echo -e "${RED}✗ Bob login failed${NC}"
fi
echo ""

# Test 4: Charlie Login (Viewer)
echo -e "${BLUE}Test 4: Charlie Login (Viewer - Read-Only)${NC}"
CHARLIE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"charlie","password":"charlie123"}')

CHARLIE_TOKEN=$(echo $CHARLIE_RESPONSE | jq -r '.access_token')
if [ "$CHARLIE_TOKEN" != "null" ] && [ -n "$CHARLIE_TOKEN" ]; then
    echo -e "${GREEN}✓ Charlie login successful${NC}"
    
    CHARLIE_CORPORA=$(curl -s -X GET "$BASE_URL/api/corpora/" \
      -H "Authorization: Bearer $CHARLIE_TOKEN")
    CHARLIE_COUNT=$(echo $CHARLIE_CORPORA | jq '. | length')
    echo "  Corpora accessible: $CHARLIE_COUNT"
    echo $CHARLIE_CORPORA | jq '.[] | "    - \(.name) (\(.permission) access)"'
    
    # Test permission enforcement
    echo -e "  ${BLUE}Testing create permission (should fail)...${NC}"
    CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/corpora/" \
      -H "Authorization: Bearer $CHARLIE_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"name":"test","display_name":"Test","gcs_bucket":"test"}')
    
    if echo $CREATE_RESPONSE | grep -q "Insufficient permissions"; then
        echo -e "  ${GREEN}✓ Permission enforcement working (create blocked)${NC}"
    else
        echo -e "  ${RED}✗ Permission enforcement failed (should have blocked)${NC}"
    fi
else
    echo -e "${RED}✗ Charlie login failed${NC}"
fi
echo ""

# Test 5: Invalid Login
echo -e "${BLUE}Test 5: Invalid Login (Wrong Password)${NC}"
INVALID_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"wrongpassword"}')

if echo $INVALID_RESPONSE | grep -q "Incorrect username or password"; then
    echo -e "${GREEN}✓ Invalid login properly rejected${NC}"
else
    echo -e "${RED}✗ Invalid login was accepted (security issue!)${NC}"
fi
echo ""

# Test 6: Token Verification
echo -e "${BLUE}Test 6: Token Verification${NC}"
if [ -n "$ALICE_TOKEN" ]; then
    ME_RESPONSE=$(curl -s -X GET "$BASE_URL/api/users/me" \
      -H "Authorization: Bearer $ALICE_TOKEN")
    
    if echo $ME_RESPONSE | jq -e '.username' > /dev/null 2>&1; then
        USERNAME=$(echo $ME_RESPONSE | jq -r '.username')
        echo -e "${GREEN}✓ Token validation working${NC}"
        echo "  Authenticated as: $USERNAME"
    else
        echo -e "${RED}✗ Token validation failed${NC}"
    fi
else
    echo -e "${RED}✗ No token to test${NC}"
fi
echo ""

echo "=========================================="
echo "Login Testing Complete!"
echo "=========================================="
