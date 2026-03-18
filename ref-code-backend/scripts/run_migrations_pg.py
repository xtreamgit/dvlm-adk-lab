#!/usr/bin/env python3
"""
Run all SQL migrations on Cloud SQL PostgreSQL database.
Uses psycopg2 to connect directly.
"""
import os
import psycopg2
import sys
from pathlib import Path

# Configuration
DB_CONFIG = {
    'host': '34.53.74.180',
    'port': 5432,
    'database': 'adk_agents_db',
    'user': 'adk_app_user',
    'password': os.environ.get('DB_PASSWORD', ''),
    'sslmode': 'require',
    'connect_timeout': 10
}

MIGRATIONS_DIR = Path('./src/database/migrations')

def run_migration(cursor, migration_file):
    """Run a single migration file."""
    migration_name = migration_file.name
    print(f"⚡ Running migration: {migration_name}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        cursor.execute(sql)
        print(f"   ✅ Completed: {migration_name}")
        return True
    except Exception as e:
        error_msg = str(e).lower()
        # Handle "already exists" errors gracefully
        if "already exists" in error_msg or "duplicate" in error_msg:
            print(f"   ⚠️  {migration_name}: {e} (treating as success)")
            return True
        else:
            print(f"   ❌ Failed: {e}")
            return False

def verify_tables(cursor):
    """Verify tables were created."""
    print("\n📋 Verifying tables...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    
    if tables:
        print(f"   Found {len(tables)} tables:")
        for (table_name,) in tables:
            print(f"   - {table_name}")
    else:
        print("   ⚠️  No tables found")
    
    return len(tables) > 0

def main():
    print("🔧 Running Database Migrations on Cloud SQL")
    print("=" * 50)
    print()
    
    # Check password
    if not DB_CONFIG['password']:
        print("❌ DB_PASSWORD environment variable not set")
        print("   Set it with: export DB_PASSWORD=your_password")
        sys.exit(1)
    
    # Get all migration files
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    
    if not migration_files:
        print("❌ No migration files found")
        sys.exit(1)
    
    print(f"📂 Found {len(migration_files)} migration files:")
    for mf in migration_files:
        print(f"   - {mf.name}")
    print()
    
    print(f"🔌 Connecting to {DB_CONFIG['host']}...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False  # Use transactions
        cursor = conn.cursor()
        
        print(f"   ✅ Connected to Cloud SQL\n")
        
        # Run each migration
        failed = []
        for migration_file in migration_files:
            try:
                if run_migration(cursor, migration_file):
                    conn.commit()
                else:
                    conn.rollback()
                    failed.append(migration_file.name)
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
                conn.rollback()
                failed.append(migration_file.name)
            print()
        
        # Verify tables
        if not failed:
            verify_tables(cursor)
        
        cursor.close()
        conn.close()
        
        # Summary
        print("\n" + "=" * 50)
        if failed:
            print(f"❌ {len(failed)} migration(s) failed:")
            for f in failed:
                print(f"   - {f}")
            sys.exit(1)
        else:
            print("✅ All migrations completed successfully")
            sys.exit(0)
            
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if your IP is allowlisted in Cloud SQL")
        print("2. Verify DB_PASSWORD is correct")
        print("3. Check if Cloud SQL instance is running")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
