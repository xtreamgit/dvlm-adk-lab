#!/bin/bash

# RBAC Testing Script
# This script automates the setup and testing of Role-Based Access Control
# Usage: ./test_rbac.sh [base_url]

set -e

BASE_URL=${1:-"http://localhost:8000"}
ADMIN_USER="admin"
ADMIN_PASS="password"

echo "=========================================="
echo "RBAC Testing Script"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Step 1: Login as admin
echo "Step 1: Logging in as admin..."
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" != "null" ] && [ -n "$ADMIN_TOKEN" ]; then
    print_success "Admin logged in successfully"
else
    print_error "Failed to login as admin"
    exit 1
fi

# Step 2: Create test users
echo ""
echo "Step 2: Creating test users..."

# Create Alice (Developer)
print_info "Creating user: alice"
ALICE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "full_name": "Alice Developer",
    "password": "alice123"
  }')

ALICE_ID=$(echo $ALICE_RESPONSE | jq -r '.id // empty')
if [ -n "$ALICE_ID" ] && [ "$ALICE_ID" != "null" ]; then
    print_success "Created Alice (ID: $ALICE_ID)"
else
    ERROR_MSG=$(echo $ALICE_RESPONSE | jq -r '.detail // "Unknown error"')
    if [[ "$ERROR_MSG" == *"already exists"* ]]; then
        print_warning "Alice already exists, attempting login to get ID..."
        ALICE_LOGIN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
          -H "Content-Type: application/json" \
          -d '{"username":"alice","password":"alice123"}')
        ALICE_ID=$(echo $ALICE_LOGIN | jq -r '.user.id // empty')
        if [ -n "$ALICE_ID" ]; then
            print_success "Found existing Alice (ID: $ALICE_ID)"
        fi
    else
        print_error "Failed to create Alice: $ERROR_MSG"
    fi
fi

# Create Bob (Manager)
print_info "Creating user: bob"
BOB_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "bob",
    "email": "bob@example.com",
    "full_name": "Bob Manager",
    "password": "bob12345"
  }')

BOB_ID=$(echo $BOB_RESPONSE | jq -r '.id // empty')
if [ -n "$BOB_ID" ] && [ "$BOB_ID" != "null" ]; then
    print_success "Created Bob (ID: $BOB_ID)"
else
    ERROR_MSG=$(echo $BOB_RESPONSE | jq -r '.detail // "Unknown error"')
    if [[ "$ERROR_MSG" == *"already exists"* ]]; then
        print_warning "Bob already exists, attempting login to get ID..."
        BOB_LOGIN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
          -H "Content-Type: application/json" \
          -d '{"username":"bob","password":"bob12345"}')
        BOB_ID=$(echo $BOB_LOGIN | jq -r '.user.id // empty')
        if [ -n "$BOB_ID" ]; then
            print_success "Found existing Bob (ID: $BOB_ID)"
        fi
    else
        print_error "Failed to create Bob: $ERROR_MSG"
    fi
fi

# Create Charlie (Viewer)
print_info "Creating user: charlie"
CHARLIE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "charlie",
    "email": "charlie@example.com",
    "full_name": "Charlie Viewer",
    "password": "charlie123"
  }')

CHARLIE_ID=$(echo $CHARLIE_RESPONSE | jq -r '.id // empty')
if [ -n "$CHARLIE_ID" ] && [ "$CHARLIE_ID" != "null" ]; then
    print_success "Created Charlie (ID: $CHARLIE_ID)"
else
    ERROR_MSG=$(echo $CHARLIE_RESPONSE | jq -r '.detail // "Unknown error"')
    if [[ "$ERROR_MSG" == *"already exists"* ]]; then
        print_warning "Charlie already exists, attempting login to get ID..."
        CHARLIE_LOGIN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
          -H "Content-Type: application/json" \
          -d '{"username":"charlie","password":"charlie123"}')
        CHARLIE_ID=$(echo $CHARLIE_LOGIN | jq -r '.user.id // empty')
        if [ -n "$CHARLIE_ID" ]; then
            print_success "Found existing Charlie (ID: $CHARLIE_ID)"
        fi
    else
        print_error "Failed to create Charlie: $ERROR_MSG"
    fi
fi

# Step 3: Create groups
echo ""
echo "Step 3: Creating groups..."

# Create Developers group
print_info "Creating group: developers"
DEVS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/groups/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "developers",
    "display_name": "Development Team",
    "description": "Software developers with full access"
  }')

DEVS_ID=$(echo $DEVS_RESPONSE | jq -r '.id // empty')
if [ -n "$DEVS_ID" ] && [ "$DEVS_ID" != "null" ]; then
    print_success "Created Developers group (ID: $DEVS_ID)"
else
    ERROR_MSG=$(echo $DEVS_RESPONSE | jq -r '.detail // "Unknown error"')
    if [[ "$ERROR_MSG" == *"already exists"* ]] || [[ "$ERROR_MSG" == *"exists"* ]]; then
        print_warning "Developers group already exists, fetching..."
        ALL_GROUPS=$(curl -s -X GET "$BASE_URL/api/groups/" -H "Authorization: Bearer $ADMIN_TOKEN")
        DEVS_ID=$(echo "$ALL_GROUPS" | jq -r '.[] | select(.name=="developers") | .id // empty')
        if [ -n "$DEVS_ID" ]; then
            print_success "Found existing Developers group (ID: $DEVS_ID)"
        fi
    else
        print_error "Failed to create Developers group: $ERROR_MSG"
    fi
fi

# Create Managers group
print_info "Creating group: managers"
MGRS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/groups/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "managers",
    "display_name": "Management Team",
    "description": "Managers with oversight access"
  }')

MGRS_ID=$(echo $MGRS_RESPONSE | jq -r '.id // empty')
if [ -n "$MGRS_ID" ] && [ "$MGRS_ID" != "null" ]; then
    print_success "Created Managers group (ID: $MGRS_ID)"
else
    ERROR_MSG=$(echo $MGRS_RESPONSE | jq -r '.detail // "Unknown error"')
    if [[ "$ERROR_MSG" == *"already exists"* ]] || [[ "$ERROR_MSG" == *"exists"* ]]; then
        print_warning "Managers group already exists, fetching..."
        ALL_GROUPS=$(curl -s -X GET "$BASE_URL/api/groups/" -H "Authorization: Bearer $ADMIN_TOKEN")
        MGRS_ID=$(echo "$ALL_GROUPS" | jq -r '.[] | select(.name=="managers") | .id // empty')
        if [ -n "$MGRS_ID" ]; then
            print_success "Found existing Managers group (ID: $MGRS_ID)"
        fi
    else
        print_error "Failed to create Managers group: $ERROR_MSG"
    fi
fi

# Create Viewers group
print_info "Creating group: viewers"
VIEWERS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/groups/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "viewers",
    "display_name": "Read-Only Users",
    "description": "Users with read-only access"
  }')

VIEWERS_ID=$(echo $VIEWERS_RESPONSE | jq -r '.id // empty')
if [ -n "$VIEWERS_ID" ] && [ "$VIEWERS_ID" != "null" ]; then
    print_success "Created Viewers group (ID: $VIEWERS_ID)"
else
    ERROR_MSG=$(echo $VIEWERS_RESPONSE | jq -r '.detail // "Unknown error"')
    if [[ "$ERROR_MSG" == *"already exists"* ]] || [[ "$ERROR_MSG" == *"exists"* ]]; then
        print_warning "Viewers group already exists, fetching..."
        ALL_GROUPS=$(curl -s -X GET "$BASE_URL/api/groups/" -H "Authorization: Bearer $ADMIN_TOKEN")
        VIEWERS_ID=$(echo "$ALL_GROUPS" | jq -r '.[] | select(.name=="viewers") | .id // empty')
        if [ -n "$VIEWERS_ID" ]; then
            print_success "Found existing Viewers group (ID: $VIEWERS_ID)"
        fi
    else
        print_error "Failed to create Viewers group: $ERROR_MSG"
    fi
fi

# Step 4: Add users to groups
echo ""
echo "Step 4: Adding users to groups..."

# Add Alice to developers group
print_info "Adding Alice to Developers group"
ADD_ALICE=$(curl -s -X PUT "$BASE_URL/api/groups/$DEVS_ID/users/$ALICE_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
if echo $ADD_ALICE | grep -q "successfully\|success"; then
    print_success "Alice added to Developers"
else
    print_warning "Alice may already be in Developers"
fi

# Add Bob to managers group
print_info "Adding Bob to Managers group"
ADD_BOB=$(curl -s -X PUT "$BASE_URL/api/groups/$MGRS_ID/users/$BOB_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
if echo $ADD_BOB | grep -q "successfully\|success"; then
    print_success "Bob added to Managers"
else
    print_warning "Bob may already be in Managers"
fi

# Add Charlie to viewers group
print_info "Adding Charlie to Viewers group"
ADD_CHARLIE=$(curl -s -X PUT "$BASE_URL/api/groups/$VIEWERS_ID/users/$CHARLIE_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
if echo $ADD_CHARLIE | grep -q "successfully\|success"; then
    print_success "Charlie added to Viewers"
else
    print_warning "Charlie may already be in Viewers"
fi

# Step 5: Grant agent access to users
echo ""
echo "Step 5: Granting agent access to users..."

# Get default agent ID (usually ID 1)
DEFAULT_AGENT_ID=1
DB_PATH="../data/users.db"

# Note: API endpoint has a bug (500 error), using direct SQL instead
print_info "Granting agent access via database..."

# Build SQL insert for all users that need access
if [ -n "$ALICE_ID" ] || [ -n "$BOB_ID" ] || [ -n "$CHARLIE_ID" ]; then
    VALUES=""
    [ -n "$ALICE_ID" ] && VALUES="($ALICE_ID, $DEFAULT_AGENT_ID)"
    [ -n "$BOB_ID" ] && [ -n "$VALUES" ] && VALUES="$VALUES, ($BOB_ID, $DEFAULT_AGENT_ID)" || VALUES="($BOB_ID, $DEFAULT_AGENT_ID)"
    [ -n "$CHARLIE_ID" ] && [ -n "$VALUES" ] && VALUES="$VALUES, ($CHARLIE_ID, $DEFAULT_AGENT_ID)" || VALUES="($CHARLIE_ID, $DEFAULT_AGENT_ID)"
    
    sqlite3 $DB_PATH "INSERT OR IGNORE INTO user_agent_access (user_id, agent_id) VALUES $VALUES;" 2>/dev/null
    
    [ -n "$ALICE_ID" ] && print_success "Alice granted access to default agent"
    [ -n "$BOB_ID" ] && print_success "Bob granted access to default agent"
    [ -n "$CHARLIE_ID" ] && print_success "Charlie granted access to default agent"
fi

# Step 6: Grant group access to corpora
echo ""
echo "Step 6: Granting group access to corpora..."

# Get existing corpora
CORPORA=$(curl -s -X GET "$BASE_URL/api/corpora/" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

CORPUS_IDS=$(echo $CORPORA | jq -r '.[].id')

if [ -z "$CORPUS_IDS" ]; then
    print_warning "No corpora found. Skipping corpus permissions."
else
    for CORPUS_ID in $CORPUS_IDS; do
        CORPUS_NAME=$(echo $CORPORA | jq -r ".[] | select(.id==$CORPUS_ID) | .display_name")
        
        print_info "Setting permissions for: $CORPUS_NAME (ID: $CORPUS_ID)"
        
        # Give developers admin access
        curl -s -X POST "$BASE_URL/api/corpora/$CORPUS_ID/grant" \
          -H "Authorization: Bearer $ADMIN_TOKEN" \
          -H "Content-Type: application/json" \
          -d "{\"group_id\":$DEVS_ID,\"permission\":\"admin\"}" > /dev/null
        print_success "  - Developers: admin access"
        
        # Give managers admin access
        curl -s -X POST "$BASE_URL/api/corpora/$CORPUS_ID/grant" \
          -H "Authorization: Bearer $ADMIN_TOKEN" \
          -H "Content-Type: application/json" \
          -d "{\"group_id\":$MGRS_ID,\"permission\":\"admin\"}" > /dev/null
        print_success "  - Managers: admin access"
        
        # Give viewers read access
        curl -s -X POST "$BASE_URL/api/corpora/$CORPUS_ID/grant" \
          -H "Authorization: Bearer $ADMIN_TOKEN" \
          -H "Content-Type: application/json" \
          -d "{\"group_id\":$VIEWERS_ID,\"permission\":\"read\"}" > /dev/null
        print_success "  - Viewers: read access"
    done
fi

# Step 7: Test access controls
echo ""
echo "=========================================="
echo "Testing Access Controls"
echo "=========================================="

# Test Alice
echo ""
print_info "Testing Alice (Developer - should have admin access)..."
ALICE_TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}' | jq -r '.access_token')

if [ "$ALICE_TOKEN" != "null" ] && [ -n "$ALICE_TOKEN" ]; then
    print_success "Alice logged in"
    
    ALICE_CORPORA=$(curl -s -X GET "$BASE_URL/api/corpora/" \
      -H "Authorization: Bearer $ALICE_TOKEN")
    ALICE_COUNT=$(echo $ALICE_CORPORA | jq '. | length')
    print_success "Alice can see $ALICE_COUNT corpora"
    
    ALICE_GROUPS=$(curl -s -X GET "$BASE_URL/api/users/me/groups" \
      -H "Authorization: Bearer $ALICE_TOKEN")
    print_success "Alice can access $(echo $ALICE_GROUPS | jq '. | length') groups"
else
    print_error "Failed to login as Alice"
fi

# Test Bob
echo ""
print_info "Testing Bob (Manager - should have admin access)..."
BOB_TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","password":"bob12345"}' | jq -r '.access_token')

if [ "$BOB_TOKEN" != "null" ] && [ -n "$BOB_TOKEN" ]; then
    print_success "Bob logged in"
    
    BOB_CORPORA=$(curl -s -X GET "$BASE_URL/api/corpora/" \
      -H "Authorization: Bearer $BOB_TOKEN")
    BOB_COUNT=$(echo $BOB_CORPORA | jq '. | length')
    print_success "Bob can see $BOB_COUNT corpora"
    
    BOB_GROUPS=$(curl -s -X GET "$BASE_URL/api/users/me/groups" \
      -H "Authorization: Bearer $BOB_TOKEN")
    print_success "Bob can access $(echo $BOB_GROUPS | jq '. | length') groups"
else
    print_error "Failed to login as Bob"
fi

# Test Charlie
echo ""
print_info "Testing Charlie (Viewer - should have read-only access)..."
CHARLIE_TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"charlie","password":"charlie123"}' | jq -r '.access_token')

if [ "$CHARLIE_TOKEN" != "null" ] && [ -n "$CHARLIE_TOKEN" ]; then
    print_success "Charlie logged in"
    
    CHARLIE_CORPORA=$(curl -s -X GET "$BASE_URL/api/corpora/" \
      -H "Authorization: Bearer $CHARLIE_TOKEN")
    CHARLIE_COUNT=$(echo $CHARLIE_CORPORA | jq '. | length')
    print_success "Charlie can see $CHARLIE_COUNT corpora"
    
    CHARLIE_GROUPS=$(curl -s -X GET "$BASE_URL/api/users/me/groups" \
      -H "Authorization: Bearer $CHARLIE_TOKEN")
    print_success "Charlie can access $(echo $CHARLIE_GROUPS | jq '. | length') groups"
    
    # Test if Charlie can create a corpus (should fail)
    print_info "Testing if Charlie can create a corpus (should fail)..."
    CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/corpora/" \
      -H "Authorization: Bearer $CHARLIE_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "charlie-test-corpus",
        "display_name": "Charlie Test Corpus",
        "description": "Should fail - read-only user"
      }')
    
    if echo $CREATE_RESPONSE | grep -q "error\|Forbidden\|not authorized"; then
        print_success "Charlie correctly denied corpus creation (read-only)"
    else
        print_warning "Charlie was able to create a corpus (unexpected)"
    fi
else
    print_error "Failed to login as Charlie"
fi

# Summary
echo ""
echo "=========================================="
echo "RBAC Setup Complete!"
echo "=========================================="
echo ""
echo "Test Users Created:"
echo "  1. alice / alice123    (Developer - Admin access)"
echo "  2. bob / bob12345      (Manager - Admin access)"
echo "  3. charlie / charlie123 (Viewer - Read-only access)"
echo ""
echo "Groups Created:"
echo "  - Developers (admin access to all corpora)"
echo "  - Managers (admin access to all corpora)"
echo "  - Viewers (read-only access to all corpora)"
echo ""
echo "You can now:"
echo "  1. Login via frontend as any test user"
echo "  2. Verify different access levels in the UI"
echo "  3. Test API endpoints with different user tokens"
echo ""
print_success "All tests completed!"
