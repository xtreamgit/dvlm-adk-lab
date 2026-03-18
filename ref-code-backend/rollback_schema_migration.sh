#!/bin/bash

# Schema Migration Rollback Script
# Reverts the migration from agent_types back to roles terminology
# Usage: ./rollback_schema_migration.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Docker container name
CONTAINER_NAME="adk-postgres-dev"
DB_NAME="adk_agents_db_dev"
DB_USER="adk_dev_user"

# Rollback file
ROLLBACK_FILE="src/database/migrations/010_rollback_agent_types_to_roles.sql"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Schema Migration Rollback: Agent Types → Roles${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "${RED}⚠️  WARNING: This will revert the schema migration!${NC}"
echo ""
echo -e "${YELLOW}This rollback will rename:${NC}"
echo "  • chatbot_agent_types → chatbot_roles"
echo "  • chatbot_tools → chatbot_permissions"
echo "  • chatbot_agent_type_tools → chatbot_role_permissions"
echo "  • chatbot_group_agent_types → chatbot_group_roles"
echo ""
echo -e "${YELLOW}All data will be preserved.${NC}"
echo -e "${YELLOW}Foreign keys will be automatically updated.${NC}"
echo ""

# Check if Docker container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}Error: Docker container '${CONTAINER_NAME}' is not running${NC}"
    exit 1
fi

# Check if rollback file exists
if [ ! -f "${ROLLBACK_FILE}" ]; then
    echo -e "${RED}Error: Rollback file not found: ${ROLLBACK_FILE}${NC}"
    exit 1
fi

# Confirm before proceeding
echo -e "${RED}⚠️  Are you sure you want to rollback the migration?${NC}"
read -p "Type 'ROLLBACK' to confirm: " -r
echo
if [[ ! $REPLY == "ROLLBACK" ]]; then
    echo -e "${YELLOW}Rollback cancelled.${NC}"
    exit 0
fi

echo -e "${BLUE}Executing rollback...${NC}"
echo ""

# Execute rollback
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" < "${ROLLBACK_FILE}"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}✅ Rollback completed successfully!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo -e "${YELLOW}The database schema has been reverted to use 'roles' terminology.${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Revert backend code changes (if any)"
    echo "  2. Revert frontend code changes (if any)"
    echo "  3. Restart backend server"
    echo "  4. Test the application"
    echo ""
else
    echo ""
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}❌ Rollback failed!${NC}"
    echo -e "${RED}============================================================${NC}"
    echo ""
    echo -e "${YELLOW}Please check the error messages above.${NC}"
    echo ""
    exit 1
fi
