#!/usr/bin/env python3
"""
Import data from JSON export to Cloud SQL PostgreSQL.
Uses psycopg2 for direct connection.
"""
import json
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
import getpass

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

EXPORT_FILE = './scripts/exported_data.json'

# Table import order (respects foreign key constraints)
IMPORT_ORDER = [
    'users',
    'user_profiles',
    'groups',
    'roles',
    'user_groups',
    'group_roles',
    'agents',
    'corpora',
    'user_agent_access',
    'group_corpus_access',
    'corpus_metadata',
    'corpus_audit_log',
    'corpus_sync_schedule',
    'user_sessions',
    'session_corpus_selections',
    'schema_migrations',
]

def import_table(cursor, table_name, data):
    """Import data into a single table."""
    if not data['rows']:
        print(f"  ⚠️  No data to import for {table_name}")
        return 0
    
    columns = data['columns']
    rows = data['rows']
    
    # Filter out auto-increment ID columns for PostgreSQL
    # PostgreSQL will auto-generate these
    if table_name != 'schema_migrations':  # Keep IDs for schema_migrations
        if 'id' in columns and columns[0] == 'id':
            # Remove id column
            columns = [c for c in columns if c != 'id']
            rows = [{k: v for k, v in row.items() if k != 'id'} for row in rows]
    
    if not rows:
        print(f"  ⚠️  No data to import for {table_name} after filtering")
        return 0
    
    # Build column list
    cols = ', '.join([f'"{col}"' for col in columns])
    placeholders = ', '.join(['%s'] * len(columns))
    
    # Build INSERT statement
    query = f'INSERT INTO {table_name} ({cols}) VALUES ({placeholders})'
    
    # Prepare data tuples
    data_tuples = [tuple(row.get(col) for col in columns) for row in rows]
    
    # Import data
    try:
        cursor.executemany(query, data_tuples)
        return len(data_tuples)
    except Exception as e:
        print(f"  ❌ Error importing {table_name}: {e}")
        raise

def reset_sequences(cursor):
    """Reset PostgreSQL sequences after importing data with IDs."""
    print("\n🔄 Resetting sequences...")
    
    # Get all tables with serial columns
    cursor.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND column_default LIKE 'nextval%'
        ORDER BY table_name
    """)
    
    for table_name, column_name in cursor.fetchall():
        # Get max ID from table
        cursor.execute(f'SELECT COALESCE(MAX("{column_name}"), 0) + 1 FROM {table_name}')
        next_val = cursor.fetchone()[0]
        
        # Reset sequence
        sequence_name = f'{table_name}_{column_name}_seq'
        try:
            cursor.execute(f"SELECT setval('{sequence_name}', {next_val}, false)")
            print(f"  ✅ Reset {sequence_name} to {next_val}")
        except Exception as e:
            print(f"  ⚠️  Could not reset {sequence_name}: {e}")

def main():
    print("📥 Importing Data to Cloud SQL")
    print("=" * 50)
    print()
    
    # Check password
    if not DB_CONFIG['password']:
        DB_CONFIG['password'] = getpass.getpass("Enter database password: ")
    
    # Load exported data
    print("📂 Loading exported data...")
    try:
        with open(EXPORT_FILE, 'r') as f:
            export_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Export file not found: {EXPORT_FILE}")
        print("   Run export_sqlite_data.py first")
        sys.exit(1)
    
    print(f"✅ Loaded data from {export_data['export_timestamp']}")
    print(f"   Total tables: {len(export_data['tables'])}")
    print()
    
    # Connect to Cloud SQL
    print(f"🔌 Connecting to {DB_CONFIG['host']}...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print(f"   ✅ Connected to Cloud SQL\n")
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
    
    # Import tables in order
    print("📥 Importing data...")
    imported_counts = {}
    
    try:
        for table_name in IMPORT_ORDER:
            if table_name not in export_data['tables']:
                print(f"  ⏭️  Table {table_name} not in export")
                continue
            
            print(f"  Importing {table_name}...", end=' ')
            count = import_table(cursor, table_name, export_data['tables'][table_name])
            imported_counts[table_name] = count
            print(f"✅ {count} rows")
        
        # Reset sequences for auto-increment columns
        reset_sequences(cursor)
        
        # Commit transaction
        conn.commit()
        print("\n✅ All data imported successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Import failed: {e}")
        cursor.close()
        conn.close()
        sys.exit(1)
    
    cursor.close()
    conn.close()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Import Summary:")
    total_rows = sum(imported_counts.values())
    for table, count in imported_counts.items():
        if count > 0:
            print(f"  {table:30} {count:5} rows")
    print(f"\n  {'TOTAL':30} {total_rows:5} rows")
    print("=" * 50)

if __name__ == '__main__':
    main()
