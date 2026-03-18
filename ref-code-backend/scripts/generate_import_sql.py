#!/usr/bin/env python3
"""
Generate a single SQL file with all data imports.
This can then be run once via gcloud sql connect.
"""
import json
import sys

EXPORT_FILE = './scripts/exported_data.json'
OUTPUT_FILE = './scripts/import_data.sql'

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

def escape_sql_value(value, column_name=''):
    """Escape value for SQL."""
    if value is None:
        return 'NULL'
    elif isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    elif isinstance(value, int):
        # Handle SQLite boolean columns (stored as 0/1)
        if column_name in ['is_active', 'is_enabled']:
            return 'TRUE' if value == 1 else 'FALSE'
        return str(value)
    elif isinstance(value, float):
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
        values = ', '.join([escape_sql_value(row.get(col), col) for col in columns])
        stmt = f"INSERT INTO {table_name} ({cols}) VALUES ({values});"
        statements.append(stmt)
    
    return statements

def main():
    print("📝 Generating Import SQL File")
    print("=" * 50)
    print()
    
    # Load exported data
    print(f"📂 Loading {EXPORT_FILE}...")
    try:
        with open(EXPORT_FILE, 'r') as f:
            export_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Export file not found: {EXPORT_FILE}")
        sys.exit(1)
    
    print(f"✅ Loaded data from {export_data['export_timestamp']}")
    print()
    
    # Generate SQL file
    print(f"📝 Generating {OUTPUT_FILE}...")
    total_statements = 0
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write("-- Data import for Cloud SQL\n")
        f.write(f"-- Generated from: {export_data['export_timestamp']}\n")
        f.write("-- Database: adk_agents_db\n")
        f.write("-- Note: No transaction wrapper - each insert is independent\n\n")
        
        for table_name in IMPORT_ORDER:
            if table_name not in export_data['tables']:
                continue
            
            table_data = export_data['tables'][table_name]
            row_count = len(table_data['rows'])
            
            print(f"  {table_name:30} {row_count:5} rows", end=' ')
            
            if row_count == 0:
                print("(skipped)")
                continue
            
            # Generate INSERT statements
            statements = generate_insert_statements(table_name, table_data)
            
            if not statements:
                print("(no data after filtering)")
                continue
            
            # Write to file
            f.write(f"-- Table: {table_name}\n")
            for stmt in statements:
                f.write(stmt + '\n')
            f.write('\n')
            
            total_statements += len(statements)
            print(f"✅ {len(statements)} statements")
        
        # Reset sequences
        f.write("-- Reset sequences\n")
        for table_name in IMPORT_ORDER:
            if table_name in export_data['tables'] and table_name != 'schema_migrations':
                seq_name = f"{table_name}_id_seq"
                f.write(f"SELECT setval('{seq_name}', (SELECT COALESCE(MAX(id), 0) + 1 FROM {table_name}), false);\n")
    
    # Summary
    print()
    print("=" * 50)
    print(f"✅ Generated {OUTPUT_FILE}")
    print(f"   Total INSERT statements: {total_statements}")
    print()
    print("To import:")
    print(f"  gcloud sql connect adk-multi-agents-db \\")
    print(f"    --database=adk_agents_db \\")
    print(f"    --user=adk_app_user \\")
    print(f"    --project=adk-rag-ma \\")
    print(f"    --quiet < {OUTPUT_FILE}")
    print("=" * 50)

if __name__ == '__main__':
    main()
