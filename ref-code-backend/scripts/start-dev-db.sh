#!/bin/bash
# Start local development PostgreSQL database

set -e

echo "🐳 Starting local PostgreSQL development database..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Start database
cd "$(dirname "$0")/.."

# Prefer Docker Compose v2 (docker compose). Fall back to legacy docker-compose.
if command -v docker-compose > /dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

$COMPOSE_CMD -f docker-compose.dev.yml up -d

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check if database is healthy
if $COMPOSE_CMD -f docker-compose.dev.yml ps | grep -q "healthy"; then
    echo "✅ PostgreSQL is ready!"
    echo ""
    echo "📊 Database Info:"
    echo "   Host: localhost"
    echo "   Port: 5433"
    echo "   Database: adk_agents_db_dev"
    echo "   User: adk_dev_user"
    echo "   Password: dev_password_123"
    echo ""
    echo "🔧 Connection String:"
    echo "   postgresql://adk_dev_user:dev_password_123@localhost:5433/adk_agents_db_dev"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. Load environment: export \$(cat .env.local | xargs)"
    echo "   2. Run migrations: python src/database/migrations/run_migrations.py"
    echo "   3. Start backend: uvicorn src.api.server:app --reload --port 8000"
else
    echo "⚠️  PostgreSQL is starting... Check status with:"
    echo "   $COMPOSE_CMD -f docker-compose.dev.yml ps"
fi
