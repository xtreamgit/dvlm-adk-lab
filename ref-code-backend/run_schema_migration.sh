#!/bin/bash

# Schema Migration Execution Script
# Executes the migration from roles to agent_types terminology
# Usage: ./run_schema_migration.sh

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

# Migration file
MIGRATION_FILE="src/database/migrations/010_rename_roles_to_agent_types.sql"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Schema Migration: Roles → Agent Types${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "${YELLOW}This migration will rename:${NC}"
echo "  • chatbot_roles → chatbot_agent_types"
echo "  • chatbot_permissions → chatbot_tools"
echo "  • chatbot_role_permissions → chatbot_agent_type_tools"
echo "  • chatbot_group_roles → chatbot_group_agent_types"
echo ""
echo -e "${YELLOW}All data will be preserved.${NC}"
echo -e "${YELLOW}Foreign keys will be automatically updated.${NC}"
echo ""

# Check if Docker container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}Error: Docker container '${CONTAINER_NAME}' is not running${NC}"
    exit 1
fi

# Check if migration file exists
if [ ! -f "${MIGRATION_FILE}" ]; then
    echo -e "${RED}Error: Migration file not found: ${MIGRATION_FILE}${NC}"
    exit 1
fi

# Confirm before proceeding
echo -e "${YELLOW}Ready to execute migration.${NC}"
read -p "Do you want to proceed? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Migration cancelled.${NC}"
    exit 0
fi

echo -e "${BLUE}Executing migration...${NC}"
echo ""

# Execute migration
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" < "${MIGRATION_FILE}"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}✅ Migration completed successfully!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Update backend code (models, routes, services)"
    echo "  2. Update frontend code (API calls, types)"
    echo "  3. Restart backend server"
    echo "  4. Test the application"
    echo ""
    echo -e "${YELLOW}If you need to rollback:${NC}"
    echo "  ./rollback_schema_migration.sh"
    echo ""
else
    echo ""
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}❌ Migration failed!${NC}"
    echo -e "${RED}============================================================${NC}"
    echo ""
    echo -e "${YELLOW}The database has been rolled back to its previous state.${NC}"
    echo -e "${YELLOW}Please check the error messages above.${NC}"
    echo ""
    exit 1
fi
