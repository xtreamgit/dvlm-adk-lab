#!/bin/bash
# Verify that migrations 004 and 005 are fully applied to Cloud SQL
# This checks both columns AND indexes

echo "Verifying Migrations 004 and 005 Completeness"
echo "============================================================================"
echo ""

cat <<'EOF' | gcloud sql connect adk-multi-agents-db --user=adk_app_user --database=adk_agents_db --project=adk-rag-ma --quiet

-- 1. Check if columns exist
SELECT 
    'Column Check' as check_type,
    column_name, 
    data_type, 
    column_default,
    CASE 
        WHEN column_name IN ('message_count', 'user_query_count') THEN '✅'
        ELSE '❌'
    END as status
FROM information_schema.columns 
WHERE table_name = 'user_sessions' 
  AND column_name IN ('message_count', 'user_query_count')
ORDER BY column_name;

-- 2. Check if index exists
SELECT 
    'Index Check' as check_type,
    indexname,
    indexdef,
    CASE 
        WHEN indexname = 'idx_sessions_user_query_count' THEN '✅'
        ELSE '❌'
    END as status
FROM pg_indexes 
WHERE tablename = 'user_sessions' 
  AND indexname = 'idx_sessions_user_query_count';

-- 3. Show full user_sessions structure
\d user_sessions

\q
EOF

echo ""
echo "============================================================================"
echo "Verification complete!"
echo ""
echo "Expected results:"
echo "  ✅ message_count column exists (Migration 004)"
echo "  ✅ user_query_count column exists (Migration 005)"
echo "  ✅ idx_sessions_user_query_count index exists (Migration 005)"
