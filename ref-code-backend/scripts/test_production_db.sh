#!/bin/bash
# Test production backend database connectivity

BACKEND_URL="https://backend-351592762922.us-west1.run.app"

echo "🧪 Testing Production Backend with Cloud SQL"
echo "=============================================="
echo ""

echo "1. Testing Authentication (database read)..."
curl -s -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.detail // .access_token // .'
echo ""

echo "2. Testing user creation (database write)..."
RANDOM_USER="test_$(date +%s)"
curl -s -X POST "$BACKEND_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$RANDOM_USER\",\"email\":\"${RANDOM_USER}@test.com\",\"password\":\"test123\",\"full_name\":\"Test User\"}" | jq '.'
echo ""

echo "3. Getting admin token..."
TOKEN=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
  echo "   ✅ Authenticated as admin"
  echo ""
  
  echo "4. Testing database queries..."
  echo "   Users count:"
  curl -s "$BACKEND_URL/api/admin/users" \
    -H "Authorization: Bearer $TOKEN" | jq 'length'
  
  echo "   Groups:"
  curl -s "$BACKEND_URL/api/groups" \
    -H "Authorization: Bearer $TOKEN" | jq -r '.[].name' | head -5
  
  echo "   Corpora:"
  curl -s "$BACKEND_URL/api/corpora/list" \
    -H "Authorization: Bearer $TOKEN" | jq -r '.[].name' | head -5
else
  echo "   ❌ Failed to authenticate"
fi

echo ""
echo "=============================================="
