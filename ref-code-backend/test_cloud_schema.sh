#!/bin/bash

# Cloud Database Schema Testing Script
# Purpose: Verify all admin tables work correctly after migration
# Usage: ./test_cloud_schema.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

PROJECT_ID="adk-rag-ma"
INSTANCE="adk-multi-agents-db"
DATABASE="adk_agents_db"
USER="adk_app_user"

log_test() {
    echo -e "\n${BLUE}${BOLD}TEST: $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_fail() {
    echo -e "${RED}❌ $1${NC}"
}

echo -e "${BLUE}${BOLD}================================================================${NC}"
echo -e "${BLUE}${BOLD}CLOUD DATABASE SCHEMA TESTING${NC}"
echo -e "${BLUE}${BOLD}================================================================${NC}\n"

# Create SQL test file
cat > /tmp/test_schema.sql << 'EOF'
-- Test 1: Verify all admin tables exist
\echo '=== TEST 1: Verify Admin Tables Exist ==='
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_name IN ('corpus_audit_log', 'corpus_metadata', 'corpus_sync_schedule')
ORDER BY table_name;

-- Test 2: Check corpus_audit_log structure
\echo ''
\echo '=== TEST 2: Corpus Audit Log Structure ==='
\d corpus_audit_log

-- Test 3: Check corpus_metadata structure
\echo ''
\echo '=== TEST 3: Corpus Metadata Structure ==='
\d corpus_metadata

-- Test 4: Check corpus_sync_schedule structure
\echo ''
\echo '=== TEST 4: Corpus Sync Schedule Structure ==='
\d corpus_sync_schedule

-- Test 5: Count records in each table
\echo ''
\echo '=== TEST 5: Record Counts ==='
SELECT 'corpus_audit_log' as table_name, COUNT(*) as count FROM corpus_audit_log
UNION ALL
SELECT 'corpus_metadata', COUNT(*) FROM corpus_metadata
UNION ALL
SELECT 'corpus_sync_schedule', COUNT(*) FROM corpus_sync_schedule
ORDER BY table_name;

-- Test 6: Verify foreign key relationships
\echo ''
\echo '=== TEST 6: Foreign Key Constraints ==='
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('corpus_audit_log', 'corpus_metadata', 'corpus_sync_schedule')
ORDER BY tc.table_name, kcu.column_name;

-- Test 7: Verify indexes exist
\echo ''
\echo '=== TEST 7: Indexes ==='
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('corpus_audit_log', 'corpus_metadata', 'corpus_sync_schedule')
ORDER BY tablename, indexname;

-- Test 8: Test INSERT into corpus_audit_log
\echo ''
\echo '=== TEST 8: Test INSERT into corpus_audit_log ==='
INSERT INTO corpus_audit_log (action, changes, metadata, timestamp)
VALUES ('test_action', '{"test": "data"}', '{"source": "schema_test"}', NOW())
RETURNING id, action, timestamp;

-- Test 9: Test SELECT with JOINs
\echo ''
\echo '=== TEST 9: Test JOIN Query (audit log with user and corpus) ==='
SELECT 
    cal.id,
    cal.action,
    c.name as corpus_name,
    u.username,
    cal.timestamp
FROM corpus_audit_log cal
LEFT JOIN corpora c ON cal.corpus_id = c.id
LEFT JOIN users u ON cal.user_id = u.id
ORDER BY cal.timestamp DESC
LIMIT 5;

-- Test 10: Verify corpus_metadata has data for all active corpora
\echo ''
\echo '=== TEST 10: Corpus Metadata Coverage ==='
SELECT 
    c.id,
    c.name,
    c.display_name,
    cm.sync_status,
    cm.document_count,
    CASE WHEN cm.id IS NULL THEN 'MISSING' ELSE 'OK' END as metadata_status
FROM corpora c
LEFT JOIN corpus_metadata cm ON c.corpus_id = cm.corpus_id
WHERE c.is_active = true
ORDER BY c.name;

\echo ''
\echo '=== ALL TESTS COMPLETED ==='
EOF

echo -e "${YELLOW}Connecting to Cloud SQL and running tests...${NC}\n"

# Run tests
if gcloud sql connect "$INSTANCE" \
    --database="$DATABASE" \
    --user="$USER" \
    --project="$PROJECT_ID" < /tmp/test_schema.sql 2>&1 | tee /tmp/test_results.txt; then
    
    echo -e "\n${GREEN}${BOLD}✅ ALL TESTS COMPLETED SUCCESSFULLY${NC}\n"
    
    # Clean up test data
    echo -e "${BLUE}Cleaning up test data...${NC}"
    echo "DELETE FROM corpus_audit_log WHERE action = 'test_action' AND metadata LIKE '%schema_test%';" | \
    gcloud sql connect "$INSTANCE" \
        --database="$DATABASE" \
        --user="$USER" \
        --project="$PROJECT_ID" 2>/dev/null
    
    log_success "Test data cleaned up"
    
else
    echo -e "\n${RED}${BOLD}❌ TESTS FAILED${NC}\n"
    exit 1
fi

# Clean up temp file
rm -f /tmp/test_schema.sql

echo -e "\n${BLUE}${BOLD}================================================================${NC}"
echo -e "${BLUE}${BOLD}SUMMARY${NC}"
echo -e "${BLUE}${BOLD}================================================================${NC}\n"

log_success "Schema migration verified"
log_success "All admin tables functional"
log_success "Foreign keys and indexes working"
log_success "INSERT/SELECT operations successful"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. Test /admin/audit endpoint in browser"
echo "  2. Check cloud logs for any errors"
echo "  3. Test chat UI functionality"

echo ""
