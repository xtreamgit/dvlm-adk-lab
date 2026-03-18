#!/bin/bash
# Run combined migration on Cloud SQL using gcloud sql connect
set -e

echo "🔧 Running Combined Migration on Cloud SQL"
echo "=============================================="
echo ""

PROJECT="adk-rag-ma"
INSTANCE="adk-multi-agents-db"
DATABASE="adk_agents_db"
MIGRATION_FILE="./scripts/combined_migration.sql"

echo "📂 Migration file: $MIGRATION_FILE"
echo "🔌 Connecting to Cloud SQL instance: $INSTANCE"
echo "📊 Database: $DATABASE"
echo ""

# Run migration using gcloud sql connect with input redirection
gcloud sql connect ${INSTANCE} \
  --database=${DATABASE} \
  --user=adk_app_user \
  --project=${PROJECT} \
  --quiet < "${MIGRATION_FILE}"

echo ""
echo "✅ Migration completed"
echo ""
echo "Verifying tables..."

# Verify tables were created
gcloud sql connect ${INSTANCE} \
  --database=${DATABASE} \
  --user=adk_app_user \
  --project=${PROJECT} \
  --quiet <<EOF
\dt
\q
EOF
