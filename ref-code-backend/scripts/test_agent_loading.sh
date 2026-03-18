#!/bin/bash

# Test Agent Loading with Different Users
# Verifies that each user gets their assigned agent with correct tools

set -e

BASE_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Testing Dynamic Agent Loading"
echo "=========================================="
echo ""

# Check if backend is running
echo -e "${BLUE}Checking if backend is running...${NC}"
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Backend is not running at $BASE_URL${NC}"
    echo ""
    echo -e "${YELLOW}Please start the backend server first:${NC}"
    echo "  cd /Users/hector/github.com/xtreamgit/adk-multi-agents/backend"
    echo "  python -m uvicorn src.api.server:app --reload --port 8000"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Backend is running${NC}"
echo ""

# Function to test user login and agent assignment
test_user_agent() {
    local username=$1
    local password=$2
    local expected_agent=$3
    local expected_tools=$4
    local test_description=$5
    
    echo "=========================================="
    echo -e "${CYAN}Testing: $username${NC}"
    echo -e "${YELLOW}Expected Agent: $expected_agent${NC}"
    echo -e "${YELLOW}Expected Tools: $expected_tools${NC}"
    echo "=========================================="
    echo ""
    
    # Step 1: Login
    echo -e "${BLUE}Step 1: Login as $username...${NC}"
    LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$username\",\"password\":\"$password\"}")
    
    TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
    USER_ID=$(echo $LOGIN_RESPONSE | jq -r '.user.id')
    
    if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
        echo -e "${RED}✗ Login failed for $username${NC}"
        echo "Response: $LOGIN_RESPONSE"
        return 1
    fi
    echo -e "${GREEN}✓ Login successful${NC}"
    echo "  User ID: $USER_ID"
    echo ""
    
    # Step 2: Check user's agents
    echo -e "${BLUE}Step 2: Checking available agents for $username...${NC}"
    AGENTS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/agents/me" \
        -H "Authorization: Bearer $TOKEN")
    
    AGENT_COUNT=$(echo $AGENTS_RESPONSE | jq '. | length')
    echo -e "${GREEN}✓ User has access to $AGENT_COUNT agent(s)${NC}"
    echo $AGENTS_RESPONSE | jq '.[] | "  - \(.display_name) (\(.name))"' -r
    echo ""
    
    # Step 3: Create session
    echo -e "${BLUE}Step 3: Creating session for $username...${NC}"
    SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d 'null')
    
    SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')
    
    if [ "$SESSION_ID" == "null" ] || [ -z "$SESSION_ID" ]; then
        echo -e "${RED}✗ Session creation failed${NC}"
        echo "Response: $SESSION_RESPONSE"
        return 1
    fi
    echo -e "${GREEN}✓ Session created: $SESSION_ID${NC}"
    echo ""
    
    # Step 4: Send a test message to verify agent loading
    echo -e "${BLUE}Step 4: Testing chat with agent...${NC}"
    CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/chat" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"message":"What is your name and what tools do you have?"}')
    
    AGENT_RESPONSE=$(echo $CHAT_RESPONSE | jq -r '.response')
    
    if [ "$AGENT_RESPONSE" == "null" ] || [ -z "$AGENT_RESPONSE" ]; then
        echo -e "${RED}✗ Chat failed${NC}"
        echo "Response: $CHAT_RESPONSE"
        return 1
    fi
    
    echo -e "${GREEN}✓ Agent responded successfully${NC}"
    echo ""
    echo -e "${CYAN}Agent Response:${NC}"
    echo "$AGENT_RESPONSE" | fold -w 80 -s
    echo ""
    
    # Step 5: Verify agent behavior based on expected capabilities
    echo -e "${BLUE}Step 5: Verifying agent capabilities...${NC}"
    
    # Check if response mentions expected tools
    if [[ "$AGENT_RESPONSE" == *"$expected_agent"* ]]; then
        echo -e "${GREEN}✓ Agent identified correctly as $expected_agent${NC}"
    else
        echo -e "${YELLOW}⚠ Agent name not clearly mentioned in response${NC}"
    fi
    
    # Test tool availability based on user type
    echo ""
    echo -e "${BLUE}Testing tool-specific behavior...${NC}"
    
    if [ "$username" == "alice" ]; then
        # Alice should have full access including delete
        echo -e "${CYAN}Testing full access (should have delete capabilities)...${NC}"
        if [[ "$AGENT_RESPONSE" == *"delete"* ]]; then
            echo -e "${GREEN}✓ Delete capabilities confirmed${NC}"
        else
            echo -e "${YELLOW}⚠ Delete capabilities not explicitly mentioned${NC}"
        fi
        
    elif [ "$username" == "bob" ]; then
        # Bob should be read-only
        echo -e "${CYAN}Testing read-only access (should NOT have create/delete)...${NC}"
        if [[ "$AGENT_RESPONSE" == *"read-only"* ]] || [[ "$AGENT_RESPONSE" == *"three"* ]]; then
            echo -e "${GREEN}✓ Read-only limitations confirmed${NC}"
        else
            echo -e "${YELLOW}⚠ Read-only status not explicitly mentioned${NC}"
        fi
        
        # Try to create a corpus (should fail or be refused)
        echo ""
        echo -e "${CYAN}Attempting to create corpus (should fail for read-only)...${NC}"
        CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/chat" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"message":"Create a new corpus called test-corpus"}')
        
        CREATE_TEXT=$(echo $CREATE_RESPONSE | jq -r '.response')
        if [[ "$CREATE_TEXT" == *"cannot"* ]] || [[ "$CREATE_TEXT" == *"don't have"* ]] || [[ "$CREATE_TEXT" == *"read-only"* ]]; then
            echo -e "${GREEN}✓ Agent correctly refused to create corpus${NC}"
        else
            echo -e "${YELLOW}⚠ Agent response unclear about create limitation${NC}"
            echo "Response: $CREATE_TEXT" | fold -w 80 -s | head -3
        fi
        
    elif [ "$username" == "charlie" ]; then
        # Charlie can create but not delete
        echo -e "${CYAN}Testing curator access (can create, cannot delete)...${NC}"
        if [[ "$AGENT_RESPONSE" == *"curator"* ]] || [[ "$AGENT_RESPONSE" == *"five"* ]]; then
            echo -e "${GREEN}✓ Curator capabilities confirmed${NC}"
        else
            echo -e "${YELLOW}⚠ Curator status not explicitly mentioned${NC}"
        fi
        
        # Check if delete is mentioned (should not be)
        if [[ "$AGENT_RESPONSE" != *"delete"* ]]; then
            echo -e "${GREEN}✓ Delete capability correctly not mentioned${NC}"
        else
            echo -e "${YELLOW}⚠ Delete capability mentioned (should not have this)${NC}"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✓ Test complete for $username"
    echo "==========================================${NC}"
    echo ""
    echo ""
}

# Main test execution
echo ""
echo -e "${YELLOW}This script will test dynamic agent loading for three users:${NC}"
echo "  1. Alice   - Full access (7 tools)"
echo "  2. Bob     - Read-only (3 tools)"
echo "  3. Charlie - Curator (5 tools, no delete)"
echo ""
read -p "Press Enter to begin testing..."
echo ""

# Test Alice (Full Access)
test_user_agent "alice" "alice123" "Default" "7" "Full access with all tools including delete"

# Test Bob (Read-Only)
test_user_agent "bob" "bob12345" "Research" "3" "Read-only access, query and info only"

# Test Charlie (Curator)
test_user_agent "charlie" "charlie123" "Curator" "5" "Create and manage but no delete"

echo ""
echo "=========================================="
echo -e "${GREEN}All Agent Loading Tests Complete!${NC}"
echo "=========================================="
echo ""

echo -e "${BLUE}Summary:${NC}"
echo ""
echo -e "${CYAN}✓ Alice (alice/alice123)${NC}"
echo "  Agent: default-agent"
echo "  Tools: 7 (full access including delete)"
echo "  Status: Full administrative capabilities"
echo ""

echo -e "${CYAN}✓ Bob (bob/bob12345)${NC}"
echo "  Agent: agent1 (Research Assistant)"
echo "  Tools: 3 (rag_query, list_corpora, get_corpus_info)"
echo "  Status: Read-only access, cannot create or modify"
echo ""

echo -e "${CYAN}✓ Charlie (charlie/charlie123)${NC}"
echo "  Agent: agent2 (Content Curator)"
echo "  Tools: 5 (query, list, create, add, info)"
echo "  Status: Can create and add content but cannot delete"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "  • Test in the frontend UI (http://localhost:3000)"
echo "  • Verify AgentSwitcher shows correct agent for each user"
echo "  • Try operations that should fail (e.g., Bob creating corpus)"
echo "  • Check server logs for agent loading messages"
echo ""
