#!/bin/bash
# Apply schema fix using adk_app_user (the user the backend uses)

set -e

echo "Applying user_sessions schema fix..."
echo "Database: adk_agents_db"
echo "User: adk_app_user"
echo "================================================================"

gcloud sql connect adk-multi-agents-db \
  --user=adk_app_user \
  --database=adk_agents_db \
  --project=adk-rag-ma \
  --quiet <<'EOF'
-- Add missing columns
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS user_query_count INTEGER DEFAULT 0;

-- Verify
\d user_sessions
EOF

echo ""
echo "✅ Schema fix applied!"
