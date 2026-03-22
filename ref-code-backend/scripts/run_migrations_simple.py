#!/usr/bin/env python3
"""
Run all SQL migrations on Cloud SQL database.
Requires gcloud CLI and database credentials.
"""
import os
import subprocess
import sys

# Configuration
PROJECT = "dvlm-adk-lab"
INSTANCE = "adk-multi-agents-db"
DATABASE = "adk_agents_db"
USER = "adk_app_user"
MIGRATIONS_DIR = "./src/database/migrations"

def run_migration(migration_file):
    """Run a single migration file."""
    migration_name = os.path.basename(migration_file)
    print(f"⚡ Running migration: {migration_name}")
    
    # Read migration file
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    # Build gcloud command
    cmd = [
        'gcloud', 'sql', 'execute', INSTANCE,
        f'--database={DATABASE}',
        f'--user={USER}',
        f'--project={PROJECT}',
        '--quiet',
        f'--query={sql_content}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"   ❌ Failed: {result.stderr}")
            return False
        print(f"   ✅ Completed: {migration_name}")
        return True
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout running {migration_name}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🔧 Running Database Migrations on Cloud SQL")
    print("=" * 50)
    print()
    
    # Get all migration files
    migration_files = sorted([
        os.path.join(MIGRATIONS_DIR, f) 
        for f in os.listdir(MIGRATIONS_DIR) 
        if f.endswith('.sql')
    ])
    
    if not migration_files:
        print("❌ No migration files found")
        sys.exit(1)
    
    print(f"📂 Found {len(migration_files)} migration files:")
    for mf in migration_files:
        print(f"   - {os.path.basename(mf)}")
    print()
    
    # Run each migration
    failed = []
    for migration_file in migration_files:
        if not run_migration(migration_file):
            failed.append(migration_file)
        print()
    
    # Summary
    print("=" * 50)
    if failed:
        print(f"❌ {len(failed)} migration(s) failed:")
        for f in failed:
            print(f"   - {os.path.basename(f)}")
        sys.exit(1)
    else:
        print("✅ All migrations completed successfully")
        print()
        print("Verifying tables...")
        
        # List tables
        cmd = [
            'gcloud', 'sql', 'execute', INSTANCE,
            f'--database={DATABASE}',
            f'--user={USER}',
            f'--project={PROJECT}',
            '--quiet',
            '--query=SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\' ORDER BY table_name;'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)

if __name__ == '__main__':
    main()
