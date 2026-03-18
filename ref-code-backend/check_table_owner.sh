#!/bin/bash
# Check who owns the user_sessions table

echo "Checking user_sessions table ownership..."

gcloud sql connect adk-multi-agents-db \
  --user=postgres \
  --database=adk_agents_db \
  --project=adk-rag-ma \
  --quiet <<'EOF'
SELECT 
    t.table_name,
    t.table_schema,
    pg_catalog.pg_get_userbyid(c.relowner) as table_owner
FROM information_schema.tables t
JOIN pg_catalog.pg_class c ON c.relname = t.table_name
WHERE t.table_name = 'user_sessions';
EOF
