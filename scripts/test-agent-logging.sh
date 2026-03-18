#!/bin/bash
# Test Script for Agent Logging Verification
# This script helps verify that agent context logging is working correctly

PROJECT_ID="adk-rag-ma"
REGION="us-west1"
LB_URL="https://34.49.46.115.nip.io"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Multi-Agent Logging Test Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Check application is accessible
echo "📋 Test 1: Check Application Accessibility"
echo "   URL: $LB_URL"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $LB_URL 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ]; then
  echo "   ✅ Application is accessible (HTTP $HTTP_CODE)"
else
  echo "   ❌ Application returned HTTP $HTTP_CODE"
  exit 1
fi
echo ""

# Test 2: Check for any errors since deployment
echo "📋 Test 2: Check for Deployment Errors"
ERROR_COUNT=$(gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=ERROR' \
  --project=$PROJECT_ID \
  --limit=100 \
  --freshness=1h \
  --format='value(timestamp)' 2>/dev/null | wc -l | tr -d ' ')

if [ "$ERROR_COUNT" = "0" ]; then
  echo "   ✅ No errors in the last hour"
else
  echo "   ⚠️  Found $ERROR_COUNT error(s). Showing recent:"
  gcloud logging read \
    'resource.type="cloud_run_revision" AND severity>=ERROR' \
    --project=$PROJECT_ID \
    --limit=3 \
    --freshness=1h \
    --format='table(timestamp,resource.labels.service_name,textPayload.slice(0:100))'
fi
echo ""

# Test 3: Instructions for manual testing
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 MANUAL TESTING REQUIRED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Please perform these actions in your browser:"
echo ""
echo "1️⃣  Open: $LB_URL"
echo "2️⃣  Login with IAP (hector@develom.com)"
echo "3️⃣  In the sidebar, select 'Agent 1'"
echo "4️⃣  Send this message: 'List all available corpora'"
echo "5️⃣  Wait 10 seconds for the request to complete"
echo ""
echo "Press ENTER when you've completed these steps..."
read -r

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Checking Logs for Agent Context..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 4: Check for agent1 logs
echo "📋 Test 4: Verify Agent 1 Logging"
sleep 3  # Give logs a moment to propagate
AGENT1_LOGS=$(gcloud logging read \
  'resource.type="cloud_run_revision" AND textPayload:"[agent1]"' \
  --project=$PROJECT_ID \
  --limit=10 \
  --freshness=5m \
  --format='value(textPayload)' 2>/dev/null)

if [ -z "$AGENT1_LOGS" ]; then
  echo "   ⚠️  No [agent1] logs found yet"
  echo "   💡 The request may still be processing, or there might be an issue"
  echo ""
  echo "   Checking for ANY recent backend logs..."
  gcloud logging read \
    'resource.type="cloud_run_revision" AND (resource.labels.service_name="backend-agent1" OR resource.labels.service_name="backend")' \
    --project=$PROJECT_ID \
    --limit=5 \
    --freshness=5m \
    --format='table(timestamp,resource.labels.service_name,textPayload.slice(0:100))'
else
  echo "   ✅ Found agent1 logs! Showing samples:"
  echo "$AGENT1_LOGS" | head -5
fi
echo ""

# Test 5: Check structured logging
echo "📋 Test 5: Verify Structured Logging"
STRUCTURED_LOGS=$(gcloud logging read \
  'resource.type="cloud_run_revision" AND jsonPayload.agent="agent1"' \
  --project=$PROJECT_ID \
  --limit=5 \
  --freshness=5m \
  --format='value(jsonPayload.agent,jsonPayload.action,jsonPayload.corpus)' 2>/dev/null)

if [ -z "$STRUCTURED_LOGS" ]; then
  echo "   ℹ️  Structured logs not found (may be using text logging only)"
else
  echo "   ✅ Structured logging working:"
  echo "$STRUCTURED_LOGS"
fi
echo ""

# Test 6: Multi-agent differentiation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 MULTI-AGENT TEST (Optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To test that different agents log separately:"
echo ""
echo "1️⃣  Switch to 'Agent 2' in the sidebar"
echo "2️⃣  Send: 'List all available corpora'"
echo "3️⃣  Switch to 'Agent 3' in the sidebar"
echo "4️⃣  Send: 'List all available corpora'"
echo ""
echo "Press ENTER when done (or press Ctrl+C to skip)..."
read -r

echo ""
echo "🔍 Checking for multi-agent logs..."
echo ""

for agent in agent1 agent2 agent3; do
  COUNT=$(gcloud logging read \
    "resource.type=\"cloud_run_revision\" AND textPayload:\"[$agent]\"" \
    --project=$PROJECT_ID \
    --limit=100 \
    --freshness=10m \
    --format='value(timestamp)' 2>/dev/null | wc -l | tr -d ' ')
  
  if [ "$COUNT" = "0" ]; then
    echo "   [$agent]: ⚠️  No logs found (not tested or no activity)"
  else
    echo "   [$agent]: ✅ Found $COUNT log entries"
  fi
done
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Final verification
TOTAL_AGENT_LOGS=$(gcloud logging read \
  'resource.type="cloud_run_revision" AND textPayload:"[agent"' \
  --project=$PROJECT_ID \
  --limit=100 \
  --freshness=10m \
  --format='value(timestamp)' 2>/dev/null | wc -l | tr -d ' ')

if [ "$TOTAL_AGENT_LOGS" = "0" ]; then
  echo "❌ ISSUE: No agent logs found"
  echo ""
  echo "Possible reasons:"
  echo "  1. Requests haven't reached the backend yet (check IAP/LB routing)"
  echo "  2. Application error preventing log output"
  echo "  3. Logs haven't propagated yet (wait 1-2 minutes)"
  echo ""
  echo "Debug commands:"
  echo "  # Check if backend received ANY requests"
  echo "  gcloud logging read 'resource.labels.service_name=\"backend-agent1\"' \\"
  echo "    --project=$PROJECT_ID --limit=20 --freshness=10m"
  echo ""
  echo "  # Check for errors"
  echo "  gcloud logging read 'severity>=ERROR' \\"
  echo "    --project=$PROJECT_ID --limit=10 --freshness=10m"
else
  echo "✅ SUCCESS: Found $TOTAL_AGENT_LOGS agent-tagged log entries!"
  echo ""
  echo "Sample logs:"
  gcloud logging read \
    'resource.type="cloud_run_revision" AND textPayload:"[agent"' \
    --project=$PROJECT_ID \
    --limit=5 \
    --freshness=10m \
    --format='table(timestamp,resource.labels.service_name,textPayload.slice(0:100))'
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Testing Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Useful commands for further testing:"
echo ""
echo "# View all agent logs"
echo "gcloud logging read 'textPayload:\"[agent\"' --project=$PROJECT_ID --limit=20"
echo ""
echo "# View specific agent logs"
echo "gcloud logging read 'textPayload:\"[agent1]\"' --project=$PROJECT_ID --limit=10"
echo ""
echo "# View structured logs"
echo "gcloud logging read 'jsonPayload.agent=~\".*\"' --project=$PROJECT_ID --limit=10"
echo ""
echo "# Stream logs in real-time"
echo "gcloud logging tail 'resource.type=\"cloud_run_revision\"' --project=$PROJECT_ID"
echo ""
