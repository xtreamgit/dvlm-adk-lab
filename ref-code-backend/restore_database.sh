#!/bin/bash

# Database Restore Script
# Purpose: Restore database from backup (if sync goes wrong)
# Usage: ./restore_database.sh <backup_file> [local|cloud]

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
LOCAL_HOST="${DB_HOST:-localhost}"
LOCAL_PORT="${DB_PORT:-5433}"
LOCAL_DB="${DB_NAME:-adk_agents_db_dev}"
LOCAL_USER="${DB_USER:-adk_dev_user}"
LOCAL_PASSWORD="${DB_PASSWORD:-dev_password_123}"

CLOUD_HOST="127.0.0.1"
CLOUD_PORT="5432"
CLOUD_DB="adk_agents_db"
CLOUD_USER="adk_app_user"
PROJECT_ID="adk-rag-ma"

restore_local() {
    local backup_file="$1"
    
    log_header "Restoring LOCAL database"
    
    log_info "Backup file: $backup_file"
    log_info "Target: $LOCAL_USER@$LOCAL_HOST:$LOCAL_PORT/$LOCAL_DB"
    
    # Decompress if needed
    if [[ "$backup_file" == *.gz ]]; then
        log_info "Decompressing backup..."
        local temp_file="${backup_file%.gz}"
        gunzip -c "$backup_file" > "$temp_file"
        backup_file="$temp_file"
    fi
    
    # Confirm
    log_warning "This will DROP and RECREATE all tables in the local database!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled"
        return 1
    fi
    
    # Restore
    log_info "Restoring database..."
    if PGPASSWORD="$LOCAL_PASSWORD" psql \
        -h "$LOCAL_HOST" \
        -p "$LOCAL_PORT" \
        -U "$LOCAL_USER" \
        -d "$LOCAL_DB" \
        -f "$backup_file"; then
        
        log_success "Local database restored successfully"
        
        # Verify
        log_info "Verifying restore..."
        local table_count=$(PGPASSWORD="$LOCAL_PASSWORD" psql \
            -h "$LOCAL_HOST" \
            -p "$LOCAL_PORT" \
            -U "$LOCAL_USER" \
            -d "$LOCAL_DB" \
            -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)
        
        log_success "Found $table_count tables in restored database"
        return 0
    else
        log_error "Restore failed"
        return 1
    fi
}

restore_cloud() {
    local backup_file="$1"
    
    log_header "Restoring CLOUD database"
    
    log_warning "⚠️ ⚠️ ⚠️  WARNING  ⚠️ ⚠️ ⚠️"
    log_warning "This will modify the PRODUCTION cloud database!"
    log_warning "This is a DESTRUCTIVE operation!"
    echo ""
    
    log_info "Backup file: $backup_file"
    log_info "Target: $CLOUD_USER@$CLOUD_HOST:$CLOUD_PORT/$CLOUD_DB"
    
    # Decompress if needed
    if [[ "$backup_file" == *.gz ]]; then
        log_info "Decompressing backup..."
        local temp_file="${backup_file%.gz}"
        gunzip -c "$backup_file" > "$temp_file"
        backup_file="$temp_file"
    fi
    
    # Double confirm for cloud
    read -p "Type 'RESTORE CLOUD DATABASE' to confirm: " confirm
    
    if [ "$confirm" != "RESTORE CLOUD DATABASE" ]; then
        log_info "Restore cancelled"
        return 1
    fi
    
    # Get password
    log_info "Retrieving cloud database password..."
    CLOUD_PASSWORD=$(gcloud secrets versions access latest --secret=db-password --project=$PROJECT_ID 2>/dev/null)
    if [ -z "$CLOUD_PASSWORD" ]; then
        log_error "Failed to retrieve cloud database password"
        return 1
    fi
    
    # Restore
    log_info "Restoring cloud database..."
    if PGPASSWORD="$CLOUD_PASSWORD" psql \
        -h "$CLOUD_HOST" \
        -p "$CLOUD_PORT" \
        -U "$CLOUD_USER" \
        -d "$CLOUD_DB" \
        -f "$backup_file"; then
        
        log_success "Cloud database restored successfully"
        
        # Verify
        log_info "Verifying restore..."
        local table_count=$(PGPASSWORD="$CLOUD_PASSWORD" psql \
            -h "$CLOUD_HOST" \
            -p "$CLOUD_PORT" \
            -U "$CLOUD_USER" \
            -d "$CLOUD_DB" \
            -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)
        
        log_success "Found $table_count tables in restored database"
        return 0
    else
        log_error "Restore failed"
        return 1
    fi
}

show_usage() {
    echo "Usage: $0 <backup_file> [local|cloud]"
    echo ""
    echo "Arguments:"
    echo "  backup_file  - Path to backup file (.sql or .sql.gz)"
    echo "  target       - Target database (local or cloud)"
    echo ""
    echo "Examples:"
    echo "  $0 backups/local_adk_agents_db_dev_20260125_110530.sql local"
    echo "  $0 backups/cloud_adk_agents_db_20260125_110545.sql.gz cloud"
    echo ""
    echo "Available backups:"
    if [ -d "backups" ]; then
        ls -lh backups/*.sql* 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    else
        echo "  No backups found in ./backups/"
    fi
}

main() {
    if [ $# -lt 2 ]; then
        log_error "Missing arguments"
        show_usage
        exit 1
    fi
    
    local backup_file="$1"
    local target="$2"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        show_usage
        exit 1
    fi
    
    log_header "Database Restore Tool"
    
    case "$target" in
        local)
            restore_local "$backup_file"
            ;;
        
        cloud)
            restore_cloud "$backup_file"
            ;;
        
        *)
            log_error "Unknown target: $target"
            show_usage
            exit 1
            ;;
    esac
}

# Run main
main "$@"
