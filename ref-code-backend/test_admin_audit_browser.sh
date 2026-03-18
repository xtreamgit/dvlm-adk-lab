#!/bin/bash

# Browser-Based Admin Audit Endpoint Test
# Opens the endpoint in browser for manual verification
# Usage: ./test_admin_audit_browser.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

ADMIN_AUDIT_URL="https://34.49.46.115.nip.io/api/admin/audit"

echo -e "${BLUE}${BOLD}================================================================${NC}"
echo -e "${BLUE}${BOLD}/ADMIN/AUDIT ENDPOINT - BROWSER TEST${NC}"
echo -e "${BLUE}${BOLD}================================================================${NC}\n"

echo -e "${YELLOW}This test requires manual verification in your browser${NC}"
echo -e "${YELLOW}IAP authentication will be handled automatically by your browser${NC}\n"

echo -e "${BLUE}Opening admin audit endpoint in browser...${NC}\n"
echo -e "URL: ${BOLD}$ADMIN_AUDIT_URL${NC}\n"

# Open in default browser
if command -v open &> /dev/null; then
    # macOS
    open "$ADMIN_AUDIT_URL"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "$ADMIN_AUDIT_URL"
elif command -v start &> /dev/null; then
    # Windows
    start "$ADMIN_AUDIT_URL"
else
    echo -e "${YELLOW}Could not auto-open browser. Please open manually:${NC}"
    echo -e "${BOLD}$ADMIN_AUDIT_URL${NC}\n"
fi

echo -e "${GREEN}${BOLD}WHAT TO VERIFY:${NC}\n"

echo "1. ✅ Browser redirects to Google login (if not already logged in)"
echo "2. ✅ After login, page loads successfully (no 404 or 500 error)"
echo "3. ✅ Page shows JSON data or formatted audit log entries"
echo "4. ✅ Data includes fields like: id, action, user_name, timestamp"
echo "5. ✅ No database errors visible in the response"

echo -e "\n${GREEN}${BOLD}EXPECTED RESPONSE FORMAT:${NC}\n"

cat << 'EOF'
[
  {
    "id": 1,
    "corpus_id": null,
    "corpus_name": null,
    "user_id": 1,
    "user_name": "alice",
    "action": "created_user",
    "changes": null,
    "metadata": null,
    "timestamp": "2026-01-22T01:59:50.416955"
  },
  {
    "id": 2,
    "corpus_id": null,
    "corpus_name": null,
    "user_id": 1,
    "user_name": "alice",
    "action": "updated_user",
    "changes": null,
    "metadata": null,
    "timestamp": "2026-01-22T02:00:18.004656"
  }
]
EOF

echo -e "\n${BLUE}${BOLD}TROUBLESHOOTING:${NC}\n"

echo "❌ 404 Not Found:"
echo "   → Check backend deployment has /admin/audit route"
echo "   → Verify Cloud Run backend service is running"
echo ""

echo "❌ 500 Internal Server Error:"
echo "   → Check cloud logs: gcloud logging read 'resource.labels.service_name=backend' --limit=20"
echo "   → Verify database tables exist (corpus_audit_log)"
echo ""

echo "❌ Empty array []:"
echo "   → Normal if no audit events have been logged yet"
echo "   → Try performing an admin action then refresh"
echo ""

echo "❌ Database error visible:"
echo "   → Run: ./sync_database_schemas.sh full"
echo "   → Verify admin tables were created successfully"
echo ""

echo -e "${YELLOW}${BOLD}After reviewing the page in your browser, report back:${NC}"
echo "  • Did the page load successfully?"
echo "  • What data (if any) was displayed?"
echo "  • Any errors visible?"

echo ""
