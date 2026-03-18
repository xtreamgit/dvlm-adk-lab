#!/bin/bash
# Test what users exist in Cloud SQL and their password hashes

echo "📋 Checking users in Cloud SQL PostgreSQL"
echo "=========================================="

gcloud sql connect adk-multi-agents-db \
  --database=adk_agents_db \
  --user=postgres \
  --project=adk-rag-ma \
  --quiet <<'EOF'
\x
SELECT username, email, is_active, created_at, LEFT(hashed_password, 30) as pwd_hash_prefix 
FROM users 
ORDER BY created_at 
LIMIT 5;
EOF
