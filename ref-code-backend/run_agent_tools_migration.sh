#!/bin/bash

# ============================================================================
# Run Agent Tools Migration (011)
# ============================================================================
# This script updates tool names and creates agent-to-tool associations
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="adk-postgres-dev"
DB_NAME="adk_agents_db_dev"
DB_USER="adk_dev_user"
MIGRATION_FILE="src/database/migrations/011_update_agent_tools.sql"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Agent Tools Migration Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker container is running
echo -e "${YELLOW}Checking Docker container...${NC}"
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}Error: Docker container '$CONTAINER_NAME' is not running${NC}"
    echo "Please start the container first"
    exit 1
fi
echo -e "${GREEN}✓ Container is running${NC}"
echo ""

# Check if migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}Error: Migration file not found: $MIGRATION_FILE${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Migration file found${NC}"
echo ""

# Show what will be changed
echo -e "${YELLOW}This migration will:${NC}"
echo "  1. Update tool names to match agent_hierarchy.py"
echo "  2. Rename 'corpus-manager' to 'admin'"
echo "  3. Create agent-to-tool associations:"
echo "     - viewer: 4 tools"
echo "     - contributor: 5 tools"
echo "     - content-manager: 6 tools"
echo "     - admin: 8 tools"
echo ""

# Confirmation prompt
read -p "Do you want to proceed? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Migration cancelled${NC}"
    exit 0
fi

# Run the migration
echo -e "${BLUE}Running migration...${NC}"
echo ""

docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" < "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Migration completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Update agent_hierarchy.py to use 'admin' instead of 'corpus-manager'"
    echo "  2. Update middleware to recognize 'admin' agent type"
    echo "  3. Restart the backend server"
    echo "  4. Test with alice user to verify tool counts"
    echo ""
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Migration failed!${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Please check the error messages above"
    exit 1
fi
