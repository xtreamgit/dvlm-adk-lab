#!/usr/bin/env python3
"""
Import data to Cloud SQL using gcloud sql connect.
Generates SQL INSERT statements and runs them via gcloud.
"""
import json
import sys
import subprocess
import tempfile

# Configuration
PROJECT = "adk-rag-ma"
INSTANCE = "adk-multi-agents-db"
DATABASE = "adk_agents_db"
USER = "adk_app_user"
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

def escape_sql_value(value):
    """Escape value for SQL."""
    if value is None:
        return 'NULL'
    elif isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        # Escape single quotes
        value_str = str(value).replace("'", "''")
        return f"'{value_str}'"

def generate_insert_statements(table_name, data):
    """Generate INSERT statements for a table."""
    if not data['rows']:
        return []
    
    columns = data['columns']
    rows = data['rows']
    
    # Filter out auto-increment ID columns for PostgreSQL (except schema_migrations)
    if table_name != 'schema_migrations':
        if 'id' in columns and columns[0] == 'id':
            columns = [c for c in columns if c != 'id']
            rows = [{k: v for k, v in row.items() if k != 'id'} for row in rows]
    
    if not rows:
        return []
    
    statements = []
    cols = ', '.join([f'"{col}"' for col in columns])
    
    for row in rows:
        values = ', '.join([escape_sql_value(row.get(col)) for col in columns])
        stmt = f"INSERT INTO {table_name} ({cols}) VALUES ({values});"
        statements.append(stmt)
    
    return statements

def run_sql_via_gcloud(sql_statements, description):
    """Run SQL statements via gcloud sql connect."""
    if not sql_statements:
        return True
    
    # Create temporary SQL file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        sql_file = f.name
        for stmt in sql_statements:
            f.write(stmt + '\n')
    
    print(f"  Running {len(sql_statements)} statements via gcloud...")
    
    # Run via gcloud sql connect
    cmd = [
        'gcloud', 'sql', 'connect', INSTANCE,
        f'--database={DATABASE}',
        f'--user={USER}',
        f'--project={PROJECT}',
        '--quiet'
    ]
    
    try:
        with open(sql_file, 'r') as f:
            result = subprocess.run(
                cmd,
                stdin=f,
                capture_output=True,
                text=True,
                timeout=60
            )
        
        if result.returncode != 0:
            print(f"  ❌ Failed: {result.stderr}")
            return False
        
        return True
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    finally:
        import os
        os.unlink(sql_file)

def main():
    print("📥 Importing Data to Cloud SQL")
    print("=" * 50)
    print()
    
    # Load exported data
    print("📂 Loading exported data...")
    try:
        with open(EXPORT_FILE, 'r') as f:
            export_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Export file not found: {EXPORT_FILE}")
        sys.exit(1)
    
    print(f"✅ Loaded data from {export_data['export_timestamp']}")
    print(f"   Total tables: {len(export_data['tables'])}")
    print()
    
    # Import tables in order
    print("📥 Importing data...")
    imported_counts = {}
    failed_tables = []
    
    for table_name in IMPORT_ORDER:
        if table_name not in export_data['tables']:
            print(f"  ⏭️  Table {table_name} not in export")
            continue
        
        table_data = export_data['tables'][table_name]
        row_count = len(table_data['rows'])
        
        print(f"  Importing {table_name}... ({row_count} rows)", end=' ')
        
        if row_count == 0:
            print("⚠️  No data")
            imported_counts[table_name] = 0
            continue
        
        # Generate INSERT statements
        statements = generate_insert_statements(table_name, table_data)
        
        if not statements:
            print("⚠️  No data after filtering")
            imported_counts[table_name] = 0
            continue
        
        # Run via gcloud
        if run_sql_via_gcloud(statements, f"import {table_name}"):
            print(f"✅ {len(statements)} rows")
            imported_counts[table_name] = len(statements)
        else:
            print(f"❌ Failed")
            failed_tables.append(table_name)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Import Summary:")
    total_rows = sum(imported_counts.values())
    for table, count in imported_counts.items():
        if count > 0:
            print(f"  {table:30} {count:5} rows")
    print(f"\n  {'TOTAL':30} {total_rows:5} rows")
    
    if failed_tables:
        print(f"\n❌ Failed tables: {', '.join(failed_tables)}")
        print("=" * 50)
        sys.exit(1)
    else:
        print("=" * 50)
        print("\n✅ All data imported successfully")
        sys.exit(0)

if __name__ == '__main__':
    main()
