#!/bin/bash
# Prepare Cloud SQL database for migration
set -e

echo "🔧 Preparing Cloud SQL Database for Migration"
echo "=============================================="
echo ""

PROJECT="adk-rag-ma"
INSTANCE="adk-multi-agents-db"
DATABASE="adk_agents_db"

# Drop and recreate database
echo "1️⃣ Dropping existing database (if exists)..."
gcloud sql databases delete ${DATABASE} \
  --instance=${INSTANCE} \
  --project=${PROJECT} \
  --quiet 2>/dev/null || echo "   Database doesn't exist or already deleted"

echo ""
echo "2️⃣ Creating fresh database..."
gcloud sql databases create ${DATABASE} \
  --instance=${INSTANCE} \
  --project=${PROJECT}

echo ""
echo "✅ Database ${DATABASE} created successfully"
echo ""
echo "Next step: Run migration scripts"
