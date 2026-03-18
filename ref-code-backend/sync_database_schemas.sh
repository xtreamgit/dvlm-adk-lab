#!/bin/bash

# Database Schema Synchronization Script
# Purpose: Compare local and cloud databases, then apply migrations to cloud
# Usage: ./sync_database_schemas.sh [compare|migrate|full]

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
PROJECT_ID="adk-rag-ma"
CLOUD_SQL_INSTANCE="adk-multi-agents-db"
CLOUD_SQL_CONNECTION="adk-rag-ma:us-west1:adk-multi-agents-db"
DATABASE_NAME="adk_agents_db"
CLOUD_USER="adk_app_user"

# Local database configuration (from .env.local)
LOCAL_HOST="${DB_HOST:-localhost}"
LOCAL_PORT="${DB_PORT:-5433}"
LOCAL_DB="${DB_NAME:-adk_agents_db_dev}"
LOCAL_USER="${DB_USER:-adk_dev_user}"
LOCAL_PASSWORD="${DB_PASSWORD:-dev_password_123}"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions
log_header() {
    echo -e "\n${BLUE}${BOLD}================================================================${NC}"
    echo -e "${BLUE}${BOLD}$1${NC}"
    echo -e "${BLUE}${BOLD}================================================================${NC}\n"
}

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

check_prerequisites() {
    log_header "Checking Prerequisites"
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found"
        echo "Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    log_success "gcloud CLI found"
    
    # Check if psql is installed
    if ! command -v psql &> /dev/null; then
        log_error "psql not found"
        echo "Install PostgreSQL client: brew install postgresql@15"
        exit 1
    fi
    log_success "psql found"
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found"
        exit 1
    fi
    log_success "Python 3 found"
    
    # Check if psycopg2 is installed
    if ! python3 -c "import psycopg2" 2>/dev/null; then
        log_warning "psycopg2 not installed"
        log_info "Installing psycopg2..."
        pip3 install psycopg2-binary
    fi
    log_success "psycopg2 available"
    
    # Check local database connection
    log_info "Testing local database connection..."
    if PGPASSWORD="$LOCAL_PASSWORD" psql -h "$LOCAL_HOST" -p "$LOCAL_PORT" -U "$LOCAL_USER" -d "$LOCAL_DB" -c "SELECT 1;" &>/dev/null; then
        log_success "Local database accessible"
    else
        log_error "Cannot connect to local database"
        log_warning "Ensure PostgreSQL is running: docker ps | grep postgres"
        exit 1
    fi
    
    echo ""
}

compare_schemas() {
    log_header "Comparing Database Schemas"
    
    log_info "Running schema comparison script..."
    
    # Set environment variables for the Python script
    export DB_HOST="$LOCAL_HOST"
    export DB_PORT="$LOCAL_PORT"
    export DB_NAME="$LOCAL_DB"
    export DB_USER="$LOCAL_USER"
    export DB_PASSWORD="$LOCAL_PASSWORD"
    
    # For cloud connection, we'll use Cloud Shell or proxy
    log_warning "For cloud database comparison, you need either:"
    log_info "  1. Cloud SQL Proxy running locally, OR"
    log_info "  2. Run this script in Cloud Shell"
    echo ""
    
    if [ -f "$SCRIPT_DIR/compare_database_schemas.py" ]; then
        python3 "$SCRIPT_DIR/compare_database_schemas.py"
        
        if [ $? -eq 0 ]; then
            log_success "Schemas are identical"
            return 0
        elif [ $? -eq 1 ]; then
            log_warning "Schema differences found - migration needed"
            return 1
        else
            log_error "Comparison failed"
            return 2
        fi
    else
        log_error "Comparison script not found: $SCRIPT_DIR/compare_database_schemas.py"
        exit 1
    fi
}

migrate_cloud_database() {
    log_header "Migrating Cloud Database"
    
    local migration_file="$SCRIPT_DIR/migrations/fix_cloud_schema.sql"
    
    if [ ! -f "$migration_file" ]; then
        log_error "Migration file not found: $migration_file"
        exit 1
    fi
    
    log_info "Migration file: $migration_file"
    echo ""
    
    # Confirm before proceeding
    log_warning "This will modify the PRODUCTION cloud database"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Migration cancelled"
        exit 0
    fi
    
    echo ""
    log_info "Connecting to Cloud SQL and applying migration..."
    
    # Apply migration via gcloud sql connect
    if gcloud sql connect "$CLOUD_SQL_INSTANCE" \
        --database="$DATABASE_NAME" \
        --user="$CLOUD_USER" \
        --project="$PROJECT_ID" < "$migration_file"; then
        
        log_success "Migration completed successfully"
        
        # Verify migration
        log_info "Verifying migration..."
        echo "SELECT COUNT(*) FROM corpus_audit_log; SELECT COUNT(*) FROM corpus_metadata;" | \
        gcloud sql connect "$CLOUD_SQL_INSTANCE" \
            --database="$DATABASE_NAME" \
            --user="$CLOUD_USER" \
            --project="$PROJECT_ID"
        
        log_success "Verification complete"
    else
        log_error "Migration failed"
        exit 1
    fi
}

backup_cloud_database() {
    log_header "Creating Cloud Database Backup"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="pre-migration-backup-$timestamp"
    
    log_info "Creating backup: $backup_name"
    
    if gcloud sql backups create \
        --instance="$CLOUD_SQL_INSTANCE" \
        --project="$PROJECT_ID" \
        --description="Backup before schema migration - $timestamp"; then
        
        log_success "Backup created successfully"
    else
        log_warning "Backup failed, but continuing..."
    fi
}

show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  compare    - Compare local and cloud database schemas only"
    echo "  migrate    - Apply migration to cloud database (with backup)"
    echo "  full       - Compare, backup, then migrate (recommended)"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 compare       # Check for differences"
    echo "  $0 migrate       # Apply fixes to cloud"
    echo "  $0 full          # Do everything (recommended)"
    echo ""
}

# Main execution
main() {
    local command="${1:-help}"
    
    case "$command" in
        compare)
            check_prerequisites
            compare_schemas
            ;;
        
        migrate)
            check_prerequisites
            backup_cloud_database
            migrate_cloud_database
            log_success "Migration complete! Test your admin panel at /admin/audit"
            ;;
        
        full)
            check_prerequisites
            
            if compare_schemas; then
                log_success "Schemas are already in sync - no migration needed"
                exit 0
            fi
            
            echo ""
            log_warning "Differences detected - proceeding with migration"
            backup_cloud_database
            migrate_cloud_database
            
            echo ""
            log_header "Post-Migration Verification"
            compare_schemas || true
            
            echo ""
            log_success "All done! Your cloud database should now match local schema"
            log_info "Test the admin panel: https://34.49.46.115.nip.io/admin/audit"
            ;;
        
        help|--help|-h)
            show_usage
            ;;
        
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
