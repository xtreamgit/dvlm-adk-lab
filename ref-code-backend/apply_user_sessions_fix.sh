#!/bin/bash
# Apply user_sessions schema fix to Cloud SQL
# Adds missing message_count and user_query_count columns

set -e

echo "Applying user_sessions schema fix to Cloud SQL..."
echo "================================================================"

# SQL commands
SQL_COMMANDS=$(cat <<'EOF'
-- Add missing columns
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS user_query_count INTEGER DEFAULT 0;

-- Verify the columns exist
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'user_sessions' 
  AND column_name IN ('message_count', 'user_query_count')
ORDER BY column_name;
EOF
)

# Execute via gcloud (uses Cloud SQL Proxy internally)
echo "$SQL_COMMANDS" | gcloud sql connect adk-multi-agents-db \
  --user=postgres \
  --database=adk_agents_db \
  --project=adk-rag-ma \
  --quiet

echo ""
echo "================================================================"
echo "✅ Schema fix applied successfully!"
