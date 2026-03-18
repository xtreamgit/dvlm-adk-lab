#!/bin/bash
# Quick fix for alice password in Cloud SQL

echo "Generating fresh bcrypt hash for alice..."
HASH=$(python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('alice123'))" 2>/dev/null)

echo "Hash: $HASH"
echo ""
echo "Updating Cloud SQL..."

# Use postgres user to update
gcloud sql connect adk-multi-agents-db \
  --database=adk_agents_db \
  --user=postgres \
  --project=adk-rag-ma <<EOF
UPDATE users SET hashed_password = '$HASH' WHERE username = 'alice';
SELECT username, email, is_active, LEFT(hashed_password, 30) as pwd_hash FROM users WHERE username = 'alice';
EOF
