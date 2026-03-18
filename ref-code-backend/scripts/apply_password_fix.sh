#!/bin/bash
# Apply password fix to Cloud SQL via Cloud SQL Proxy

echo "🔧 Resetting alice password in Cloud SQL..."
echo ""

# Get the fresh bcrypt hash
HASH=$(python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('alice123'))")

echo "Generated hash: $HASH"
echo ""

# Update via psql through gcloud
gcloud sql connect adk-multi-agents-db \
  --database=adk_agents_db \
  --user=adk_app_user \
  --project=adk-rag-ma \
  --quiet <<EOF
UPDATE users SET hashed_password = '$HASH' WHERE username = 'alice';
SELECT username, email, is_active FROM users WHERE username = 'alice';
EOF

echo ""
echo "✅ Password updated. Testing login..."
sleep 2

curl -s -X POST "https://backend-351592762922.us-west1.run.app/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}' | jq '.'
