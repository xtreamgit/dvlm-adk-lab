#!/bin/bash
# Verify Cloud SQL schema completeness
# Check what migrations have been applied and what's missing

set -e

echo "Verifying Cloud SQL Schema Completeness"
echo "========================================================================"
echo ""

# Check schema_migrations table
echo "1. Checking applied migrations..."
echo "----------------------------------------------------------------"

gcloud sql connect adk-multi-agents-db \
  --user=adk_app_user \
  --database=adk_agents_db \
  --project=adk-rag-ma \
  --quiet <<'EOF'

-- Check if schema_migrations table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'schema_migrations'
) AS migration_table_exists;

-- If it exists, show what's been applied
SELECT 
    id, 
    migration_name, 
    applied_at 
FROM schema_migrations 
ORDER BY id;

-- Check user_sessions table structure
\d user_sessions

-- Check if the index from migration 005 exists
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'user_sessions' 
AND indexname = 'idx_sessions_user_query_count';

\q
EOF

echo ""
echo "========================================================================"
echo "Schema verification complete!"
