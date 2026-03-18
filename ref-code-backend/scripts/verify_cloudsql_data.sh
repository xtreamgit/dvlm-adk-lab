#!/bin/bash
# Verify data exists in Cloud SQL

echo "🔍 Checking Cloud SQL Data"
echo "==========================="
echo ""

gcloud sql connect adk-multi-agents-db \
  --database=adk_agents_db \
  --user=adk_app_user \
  --project=adk-rag-ma \
  --quiet <<'EOF'
SELECT 'Total Users:' as info, COUNT(*) as count FROM users;
SELECT 'Alice user:' as info, username, email, is_active FROM users WHERE username='alice';
SELECT 'User passwords (hashed):' as info, username, LEFT(hashed_password, 20) as pwd_prefix FROM users LIMIT 3;
EOF
