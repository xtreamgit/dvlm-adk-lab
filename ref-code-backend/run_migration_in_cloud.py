#!/usr/bin/env python3
"""
Run migration via Cloud Run backend's existing database connection.
This script creates a temporary Cloud Run job to execute the migration.
"""

import subprocess
import json

# The migration SQL
MIGRATION_SQL = """
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS user_query_count INTEGER DEFAULT 0;
"""

# Create a simple Python script to execute via gcloud run jobs
migration_script = """
import sys
import os
sys.path.insert(0, '/app/src')
from database.connection import get_db_connection

print("Running user_sessions schema migration...")
with get_db_connection() as conn:
    cursor = conn.cursor()
    
    # Add message_count
    cursor.execute("ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0")
    conn.commit()
    print("✅ Added message_count column")
    
    # Add user_query_count  
    cursor.execute("ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS user_query_count INTEGER DEFAULT 0")
    conn.commit()
    print("✅ Added user_query_count column")
    
    # Verify
    cursor.execute(\"\"\"
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'user_sessions' 
        AND column_name IN ('message_count', 'user_query_count')
    \"\"\")
    cols = [row[0] for row in cursor.fetchall()]
    print(f"✅ Verified columns: {cols}")

print("Migration complete!")
"""

print("Migration SQL to execute:")
print("=" * 80)
print(MIGRATION_SQL)
print("=" * 80)
print("\nTo execute this migration, run the following command:")
print()
print('gcloud run jobs create user-sessions-migration \\')
print('  --image=us-west1-docker.pkg.dev/adk-rag-ma/cloud-run-repo1/backend:latest \\')
print('  --region=us-west1 \\')
print('  --project=adk-rag-ma \\')
print('  --set-env-vars="DB_TYPE=postgresql,DB_NAME=adk_agents_db,DB_USER=adk_app_user,DB_HOST=/cloudsql/adk-rag-ma:us-west1:adk-multi-agents-db,CLOUD_SQL_CONNECTION_NAME=adk-rag-ma:us-west1:adk-multi-agents-db" \\')
print('  --set-secrets=DB_PASSWORD=db-password:latest \\')
print('  --set-cloudsql-instances=adk-rag-ma:us-west1:adk-multi-agents-db \\')
print('  --command=python3 \\')
print('  --args=-c \\')
print(f"  --args='{migration_script}' \\")
print('  --service-account=backend-sa@adk-rag-ma.iam.gserviceaccount.com')
print()
print("Then execute with: gcloud run jobs execute user-sessions-migration --region=us-west1 --project=adk-rag-ma")
