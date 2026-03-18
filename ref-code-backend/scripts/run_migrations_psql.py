#!/usr/bin/env python3
"""
Run all SQL migrations on Cloud SQL database using psql.
Requires psql to be installed.
"""
import os
import subprocess
import sys
import getpass

# Configuration
INSTANCE_IP = "34.53.74.180"  # From gcloud sql instances describe
DATABASE = "adk_agents_db"
USER = "adk_app_user"
MIGRATIONS_DIR = "./src/database/migrations"

def run_migration(migration_file, password):
    """Run a single migration file using psql."""
    migration_name = os.path.basename(migration_file)
    print(f"⚡ Running migration: {migration_name}")
    
    # Build psql command
    env = os.environ.copy()
    env['PGPASSWORD'] = password
    
    cmd = [
        'psql',
        f'host={INSTANCE_IP}',
        f'dbname={DATABASE}',
        f'user={USER}',
        'sslmode=require',
        '-f', migration_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
        if result.returncode != 0:
            print(f"   ❌ Failed: {result.stderr}")
            return False
        if result.stdout:
            print(f"   {result.stdout}")
        print(f"   ✅ Completed: {migration_name}")
        return True
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout running {migration_name}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def verify_tables(password):
    """Verify tables were created."""
    print("\n📋 Verifying tables created...")
    
    env = os.environ.copy()
    env['PGPASSWORD'] = password
    
    cmd = [
        'psql',
        f'host={INSTANCE_IP}',
        f'dbname={DATABASE}',
        f'user={USER}',
        'sslmode=require',
        '-c', "\\dt"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"❌ Failed to list tables: {result.stderr}")

def main():
    print("🔧 Running Database Migrations on Cloud SQL")
    print("=" * 50)
    print()
    
    # Check if psql is available
    try:
        subprocess.run(['psql', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ psql not found. Please install PostgreSQL client:")
        print("   brew install postgresql")
        sys.exit(1)
    
    # Get password
    password = os.environ.get('DB_PASSWORD')
    if not password:
        password = getpass.getpass(f"Enter password for {USER}@{INSTANCE_IP}: ")
    
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
        if not run_migration(migration_file, password):
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
        verify_tables(password)

if __name__ == '__main__':
    main()
