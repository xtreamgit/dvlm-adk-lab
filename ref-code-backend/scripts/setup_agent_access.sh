#!/bin/bash

# Setup Agent Access for Test Users
# Assigns different agents with different tool sets to users

set -e

BASE_URL="http://localhost:8000"
DB_PATH="../data/users.db"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Setting Up Agent Access for Test Users"
echo "=========================================="
echo ""

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}Error: Database not found at $DB_PATH${NC}"
    echo "Please run migrations first: python src/database/migrations/run_migrations.py"
    exit 1
fi

echo -e "${BLUE}Step 1: Checking current agent assignments...${NC}"
echo ""
sqlite3 $DB_PATH << EOF
.headers on
.mode column
SELECT 
    u.id as user_id,
    u.username,
    a.id as agent_id,
    a.name as agent_name,
    a.display_name
FROM users u
LEFT JOIN user_agent_access uaa ON u.id = uaa.user_id
LEFT JOIN agents a ON uaa.agent_id = a.id
ORDER BY u.username;
EOF
echo ""

echo -e "${BLUE}Step 2: Clearing existing agent assignments...${NC}"
sqlite3 $DB_PATH "DELETE FROM user_agent_access WHERE user_id IN (SELECT id FROM users WHERE username IN ('alice', 'bob', 'charlie'));"
echo -e "${GREEN}✓ Cleared existing assignments${NC}"
echo ""

echo -e "${BLUE}Step 3: Assigning agents to test users...${NC}"
echo ""

# Alice: Default agent (full access - all 7 tools)
echo -e "${YELLOW}Alice → Default Agent (Full Access)${NC}"
echo "  Tools: rag_query, list_corpora, create_corpus, add_data, get_corpus_info, delete_corpus, delete_document"
sqlite3 $DB_PATH << EOF
INSERT INTO user_agent_access (user_id, agent_id)
SELECT u.id, a.id
FROM users u, agents a
WHERE u.username = 'alice' AND a.name = 'default-agent';
EOF
echo -e "${GREEN}✓ Alice assigned to default-agent${NC}"
echo ""

# Bob: Agent1 (read-only - 3 tools)
echo -e "${YELLOW}Bob → Research Assistant Agent (Read-Only)${NC}"
echo "  Tools: rag_query, list_corpora, get_corpus_info"
sqlite3 $DB_PATH << EOF
INSERT INTO user_agent_access (user_id, agent_id)
SELECT u.id, a.id
FROM users u, agents a
WHERE u.username = 'bob' AND a.name = 'agent1';
EOF
echo -e "${GREEN}✓ Bob assigned to agent1 (read-only)${NC}"
echo ""

# Charlie: Agent2 (curator - 5 tools, no delete)
echo -e "${YELLOW}Charlie → Content Curator Agent (Create & Manage)${NC}"
echo "  Tools: rag_query, list_corpora, create_corpus, add_data, get_corpus_info"
sqlite3 $DB_PATH << EOF
INSERT INTO user_agent_access (user_id, agent_id)
SELECT u.id, a.id
FROM users u, agents a
WHERE u.username = 'charlie' AND a.name = 'agent2';
EOF
echo -e "${GREEN}✓ Charlie assigned to agent2 (curator)${NC}"
echo ""

echo -e "${BLUE}Step 4: Setting default agents for users...${NC}"
sqlite3 $DB_PATH << EOF
-- Alice gets default-agent
UPDATE users SET default_agent_id = (SELECT id FROM agents WHERE name = 'default-agent')
WHERE username = 'alice';

-- Bob gets agent1
UPDATE users SET default_agent_id = (SELECT id FROM agents WHERE name = 'agent1')
WHERE username = 'bob';

-- Charlie gets agent2
UPDATE users SET default_agent_id = (SELECT id FROM agents WHERE name = 'agent2')
WHERE username = 'charlie';
EOF
echo -e "${GREEN}✓ Default agents set${NC}"
echo ""

echo -e "${BLUE}Step 5: Verifying agent assignments...${NC}"
echo ""
sqlite3 $DB_PATH << EOF
.headers on
.mode column
SELECT 
    u.id as user_id,
    u.username,
    u.default_agent_id,
    a.id as agent_id,
    a.name as agent_name,
    a.display_name,
    a.config_path
FROM users u
JOIN user_agent_access uaa ON u.id = uaa.user_id
JOIN agents a ON uaa.agent_id = a.id
WHERE u.username IN ('alice', 'bob', 'charlie')
ORDER BY u.username;
EOF
echo ""

echo -e "${GREEN}=========================================="
echo "Agent Access Setup Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  • Alice  → default-agent (7 tools: full access)"
echo "  • Bob    → agent1 (3 tools: read-only)"
echo "  • Charlie → agent2 (5 tools: curator)"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Restart the backend server"
echo "  2. Test login with each user"
echo "  3. Verify different agent behaviors"
echo ""
