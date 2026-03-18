#!/bin/bash

# Database Backup Script for PostgreSQL
# Creates a full backup of the database before schema migration
# Usage: ./backup_database.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-adk_agents_db}"
DB_USER="${DB_USER:-adk_app_user}"

# Backup configuration
BACKUP_DIR="./database_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql"
BACKUP_COMPRESSED="${BACKUP_FILE}.gz"

echo -e "${YELLOW}=== PostgreSQL Database Backup ===${NC}"
echo "Database: ${DB_NAME}"
echo "Host: ${DB_HOST}"
echo "User: ${DB_USER}"
echo "Timestamp: ${TIMESTAMP}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Check if pg_dump is available
if ! command -v pg_dump &> /dev/null; then
    echo -e "${RED}Error: pg_dump command not found${NC}"
    echo "Please install PostgreSQL client tools"
    exit 1
fi

# Perform backup
echo -e "${YELLOW}Creating backup...${NC}"

# Handle Cloud SQL Unix socket connection
if [[ "$DB_HOST" == /cloudsql/* ]]; then
    echo "Using Cloud SQL Unix socket connection"
    pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        --format=plain \
        --no-owner \
        --no-acl \
        --verbose \
        > "$BACKUP_FILE" 2>&1
else
    # Standard TCP connection
    PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --format=plain \
        --no-owner \
        --no-acl \
        --verbose \
        > "$BACKUP_FILE" 2>&1
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup created successfully${NC}"
    
    # Compress backup
    echo -e "${YELLOW}Compressing backup...${NC}"
    gzip "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backup compressed successfully${NC}"
        
        # Display backup info
        BACKUP_SIZE=$(du -h "$BACKUP_COMPRESSED" | cut -f1)
        echo ""
        echo -e "${GREEN}=== Backup Complete ===${NC}"
        echo "Backup file: ${BACKUP_COMPRESSED}"
        echo "Backup size: ${BACKUP_SIZE}"
        echo ""
        
        # List recent backups
        echo -e "${YELLOW}Recent backups:${NC}"
        ls -lh "${BACKUP_DIR}" | tail -n 5
        
        # Create a symlink to latest backup
        ln -sf "$(basename "$BACKUP_COMPRESSED")" "${BACKUP_DIR}/latest_backup.sql.gz"
        echo ""
        echo -e "${GREEN}Latest backup symlink created: ${BACKUP_DIR}/latest_backup.sql.gz${NC}"
        
        exit 0
    else
        echo -e "${RED}❌ Failed to compress backup${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Backup failed${NC}"
    exit 1
fi
