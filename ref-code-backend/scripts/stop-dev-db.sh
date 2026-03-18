#!/bin/bash
# Stop local development PostgreSQL database

set -e

echo "🛑 Stopping local PostgreSQL development database..."

cd "$(dirname "$0")/.."
docker-compose -f docker-compose.dev.yml down

echo "✅ PostgreSQL stopped!"
echo ""
echo "💡 To start again: ./scripts/start-dev-db.sh"
echo "💡 To delete all data: docker-compose -f docker-compose.dev.yml down -v"
