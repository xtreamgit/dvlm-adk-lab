#!/bin/bash

# Database Backup Script for Dockerized PostgreSQL
# Creates a full backup of the PostgreSQL database running in Docker container
# Usage: ./backup_docker_database.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Docker container name
CONTAINER_NAME="adk-postgres-dev"

# Database configuration
DB_NAME="adk_agents_db_dev"
DB_USER="adk_dev_user"

# Backup configuration
BACKUP_DIR="./database_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql"
BACKUP_COMPRESSED="${BACKUP_FILE}.gz"

echo -e "${YELLOW}=== PostgreSQL Database Backup (Docker) ===${NC}"
echo "Container: ${CONTAINER_NAME}"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Timestamp: ${TIMESTAMP}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Check if Docker container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}Error: Docker container '${CONTAINER_NAME}' is not running${NC}"
    echo "Please start the container first"
    exit 1
fi

echo -e "${YELLOW}Creating backup...${NC}"

# Execute pg_dump inside the Docker container
docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" \
    --format=plain \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    > "${BACKUP_FILE}" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup created successfully${NC}"
    
    # Compress backup
    echo -e "${YELLOW}Compressing backup...${NC}"
    gzip "${BACKUP_FILE}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backup compressed successfully${NC}"
        
        # Display backup info
        BACKUP_SIZE=$(du -h "${BACKUP_COMPRESSED}" | cut -f1)
        echo ""
        echo -e "${GREEN}=== Backup Complete ===${NC}"
        echo "Backup file: ${BACKUP_COMPRESSED}"
        echo "Backup size: ${BACKUP_SIZE}"
        echo ""
        
        # List recent backups
        echo -e "${YELLOW}Recent backups:${NC}"
        ls -lht "${BACKUP_DIR}"/backup_*.sql.gz 2>/dev/null | head -n 5 | awk '{print "  " $9 " (" $5 ") - " $6 " " $7 " " $8}'
        
        # Create a symlink to latest backup
        ln -sf "$(basename "${BACKUP_COMPRESSED}")" "${BACKUP_DIR}/latest_backup.sql.gz"
        echo ""
        echo -e "${GREEN}Latest backup symlink created: ${BACKUP_DIR}/latest_backup.sql.gz${NC}"
        
        # Show table counts
        echo ""
        echo -e "${YELLOW}Database statistics:${NC}"
        docker exec -t "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_rows
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
            LIMIT 10;
        " 2>/dev/null || echo "  (Statistics not available)"
        
        echo ""
        echo -e "${GREEN}✅ Backup completed successfully!${NC}"
        echo ""
        
        exit 0
    else
        echo -e "${RED}❌ Failed to compress backup${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Backup failed${NC}"
    exit 1
fi
