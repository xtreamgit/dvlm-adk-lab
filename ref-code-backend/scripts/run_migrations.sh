#!/bin/bash
# Run all migrations on Cloud SQL database
set -e

echo "🔧 Running Database Migrations on Cloud SQL"
echo "=============================================="
echo ""

PROJECT="dvlm-adk-lab"
INSTANCE="adk-multi-agents-db"
DATABASE="adk_agents_db"

# Get the directory where migrations are stored
MIGRATIONS_DIR="./src/database/migrations"

echo "📂 Migration files:"
ls -1 ${MIGRATIONS_DIR}/*.sql | sort
echo ""

# Run each migration in order
for migration_file in ${MIGRATIONS_DIR}/*.sql; do
    migration_name=$(basename "$migration_file")
    echo "⚡ Running migration: $migration_name"
    
    gcloud sql connect ${INSTANCE} \
        --database=${DATABASE} \
        --user=adk_app_user \
        --project=${PROJECT} \
        --quiet < "$migration_file"
    
    echo "   ✅ Completed: $migration_name"
    echo ""
done

echo "✅ All migrations completed successfully"
echo ""
echo "Verifying tables..."
gcloud sql connect ${INSTANCE} \
    --database=${DATABASE} \
    --user=adk_app_user \
    --project=${PROJECT} \
    --quiet <<EOF
\dt
EOF
