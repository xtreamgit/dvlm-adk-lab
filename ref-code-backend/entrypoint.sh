#!/bin/bash
set -e

echo "🔧 Running database migrations..."
python src/database/migrations/run_migrations.py

echo "🔧 Adding missing columns to corpus_metadata (non-blocking)..."
python add_missing_columns.py || echo "⚠️  Column additions skipped - will retry on next startup"

echo "🚀 Starting FastAPI server..."
exec python src/api/server.py
