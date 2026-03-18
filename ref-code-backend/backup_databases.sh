#!/bin/bash

# Database Backup Script
# Purpose: Backup both local and cloud PostgreSQL databases before syncing
# Usage: ./backup_databases.sh [local|cloud|both]

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "\n${BLUE}================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================${NC}\n"
}

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Local database config
LOCAL_HOST="${DB_HOST:-localhost}"
LOCAL_PORT="${DB_PORT:-5433}"
LOCAL_DB="${DB_NAME:-adk_agents_db_dev}"
LOCAL_USER="${DB_USER:-adk_dev_user}"
LOCAL_PASSWORD="${DB_PASSWORD:-dev_password_123}"

# Cloud database config
CLOUD_HOST="${CLOUD_DB_HOST:-127.0.0.1}"  # Via Cloud SQL Proxy
CLOUD_PORT="${CLOUD_DB_PORT:-5432}"
CLOUD_DB="adk_agents_db"
CLOUD_USER="adk_app_user"
PROJECT_ID="adk-rag-ma"
CLOUD_SQL_INSTANCE="adk-multi-agents-db"

# Create backup directory
mkdir -p "$BACKUP_DIR"

backup_local() {
    log_header "Backing up LOCAL database"
    
    local backup_file="$BACKUP_DIR/local_${LOCAL_DB}_${TIMESTAMP}.sql"
    
    log_info "Database: $LOCAL_USER@$LOCAL_HOST:$LOCAL_PORT/$LOCAL_DB"
    log_info "Backup file: $backup_file"
    
    # Check if Docker is available
    if command -v docker &> /dev/null; then
        # Check if postgres container is running
        if docker ps --format '{{.Names}}' | grep -q postgres; then
            log_info "Using Docker container's pg_dump (version-matched)..."
            
            # Get the container name
            local container_name=$(docker ps --format '{{.Names}}' | grep postgres | head -n1)
            log_info "Container: $container_name"
            
            # Perform backup using docker exec
            log_info "Starting backup..."
            if docker exec "$container_name" pg_dump \
                -U "$LOCAL_USER" \
                -d "$LOCAL_DB" \
                --clean \
                --if-exists \
                --no-owner \
                --no-acl > "$backup_file"; then
                
                local size=$(du -h "$backup_file" | cut -f1)
                log_success "Local database backed up successfully"
                log_info "File: $backup_file"
                log_info "Size: $size"
                
                # Create a compressed version
                log_info "Compressing backup..."
                gzip -c "$backup_file" > "${backup_file}.gz"
                local gz_size=$(du -h "${backup_file}.gz" | cut -f1)
                log_success "Compressed: ${backup_file}.gz ($gz_size)"
                
                return 0
            else
                log_error "Local database backup failed"
                return 1
            fi
        else
            log_error "PostgreSQL Docker container not running"
            log_info "Start it with: docker-compose up -d postgres"
            return 1
        fi
    else
        log_error "Docker not found - cannot backup local database"
        log_info "Local database is running in Docker, Docker is required for backup"
        return 1
    fi
}

backup_cloud() {
    log_header "Backing up CLOUD database"
    
    local backup_file="$BACKUP_DIR/cloud_${CLOUD_DB}_${TIMESTAMP}.sql"
    
    log_info "Database: $CLOUD_USER@$CLOUD_HOST:$CLOUD_PORT/$CLOUD_DB"
    log_info "Backup file: $backup_file"
    
    # Check if Cloud SQL Proxy is running
    if ! lsof -i :$CLOUD_PORT | grep -q LISTEN; then
        log_error "Cloud SQL Proxy not running on port $CLOUD_PORT"
        log_info "Start it with:"
        log_info "  cloud-sql-proxy $PROJECT_ID:us-west1:$CLOUD_SQL_INSTANCE --port $CLOUD_PORT"
        return 1
    fi
    
    # Get cloud password from Secret Manager
    log_info "Retrieving cloud database password..."
    CLOUD_PASSWORD=$(gcloud secrets versions access latest --secret=db-password --project=$PROJECT_ID 2>/dev/null)
    if [ -z "$CLOUD_PASSWORD" ]; then
        log_error "Failed to retrieve cloud database password"
        log_info "Ensure you have access to Secret Manager"
        return 1
    fi
    log_success "Password retrieved"
    
    # Check connectivity
    if ! PGPASSWORD="$CLOUD_PASSWORD" psql -h "$CLOUD_HOST" -p "$CLOUD_PORT" -U "$CLOUD_USER" -d "$CLOUD_DB" -c "SELECT 1;" &>/dev/null; then
        log_error "Cannot connect to cloud database via proxy"
        return 1
    fi
    
    # Perform backup
    log_info "Starting backup (this may take a minute)..."
    if PGPASSWORD="$CLOUD_PASSWORD" pg_dump \
        -h "$CLOUD_HOST" \
        -p "$CLOUD_PORT" \
        -U "$CLOUD_USER" \
        -d "$CLOUD_DB" \
        --clean \
        --if-exists \
        --no-owner \
        --no-acl \
        -f "$backup_file"; then
        
        local size=$(du -h "$backup_file" | cut -f1)
        log_success "Cloud database backed up successfully"
        log_info "File: $backup_file"
        log_info "Size: $size"
        
        # Create a compressed version
        log_info "Compressing backup..."
        gzip -c "$backup_file" > "${backup_file}.gz"
        local gz_size=$(du -h "${backup_file}.gz" | cut -f1)
        log_success "Compressed: ${backup_file}.gz ($gz_size)"
        
        # Also create a Cloud SQL backup (optional)
        log_info "Creating Cloud SQL automated backup..."
        if gcloud sql backups create \
            --instance="$CLOUD_SQL_INSTANCE" \
            --project="$PROJECT_ID" \
            --description="Manual backup before sync - $TIMESTAMP" 2>/dev/null; then
            log_success "Cloud SQL automated backup created"
        else
            log_warning "Cloud SQL automated backup failed (but pg_dump succeeded)"
        fi
        
        return 0
    else
        log_error "Cloud database backup failed"
        return 1
    fi
}

show_usage() {
    echo "Usage: $0 [local|cloud|both]"
    echo ""
    echo "Options:"
    echo "  local    - Backup local PostgreSQL database only"
    echo "  cloud    - Backup cloud Cloud SQL database only"
    echo "  both     - Backup both databases (default)"
    echo ""
    echo "Examples:"
    echo "  $0 local      # Quick local backup"
    echo "  $0 cloud      # Cloud backup only"
    echo "  $0 both       # Backup everything (recommended)"
    echo ""
}

main() {
    local mode="${1:-both}"
    
    log_header "Database Backup Tool"
    log_info "Timestamp: $TIMESTAMP"
    log_info "Backup directory: $BACKUP_DIR"
    echo ""
    
    case "$mode" in
        local)
            backup_local
            ;;
        
        cloud)
            backup_cloud
            ;;
        
        both)
            local local_result=0
            local cloud_result=0
            
            backup_local || local_result=$?
            echo ""
            backup_cloud || cloud_result=$?
            
            echo ""
            log_header "Backup Summary"
            
            if [ $local_result -eq 0 ]; then
                log_success "Local backup: SUCCESS"
            else
                log_error "Local backup: FAILED"
            fi
            
            if [ $cloud_result -eq 0 ]; then
                log_success "Cloud backup: SUCCESS"
            else
                log_error "Cloud backup: FAILED"
            fi
            
            if [ $local_result -eq 0 ] && [ $cloud_result -eq 0 ]; then
                echo ""
                log_success "✨ All backups completed successfully!"
                log_info "Backups saved in: $BACKUP_DIR/"
                log_info "You can now safely run sync_database_data.py"
                return 0
            else
                echo ""
                log_error "Some backups failed - review errors above"
                return 1
            fi
            ;;
        
        help|--help|-h)
            show_usage
            ;;
        
        *)
            log_error "Unknown option: $mode"
            show_usage
            exit 1
            ;;
    esac
}

# Run main
main "$@"
