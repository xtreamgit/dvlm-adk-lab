#!/usr/bin/env python3
"""
Database Schema Comparison Tool

Compares local and cloud PostgreSQL database schemas to identify differences.
Reports missing tables, columns, and structural mismatches.
"""

import os
import sys
import json
from typing import Dict, List, Set, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def get_local_connection():
    """Connect to local PostgreSQL database."""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5433'),
        database=os.getenv('DB_NAME', 'adk_agents_db_dev'),
        user=os.getenv('DB_USER', 'adk_dev_user'),
        password=os.getenv('DB_PASSWORD', 'dev_password_123')
    )


def get_cloud_connection():
    """
    Connect to Cloud SQL database.
    
    Note: This requires either:
    1. Cloud SQL Proxy running locally, or
    2. Direct connection via Cloud Shell
    
    Set CLOUD_DB_HOST environment variable to override default.
    """
    cloud_host = os.getenv('CLOUD_DB_HOST', '/cloudsql/adk-rag-ma:us-west1:adk-multi-agents-db')
    
    return psycopg2.connect(
        host=cloud_host,
        database='adk_agents_db',
        user='adk_app_user',
        password=os.getenv('CLOUD_DB_PASSWORD', '')  # Set via env var
    )


def get_schema_info(conn) -> Dict:
    """Extract complete schema information from database."""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Get all tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        
        schema_info = {
            'tables': {},
            'indexes': {},
            'foreign_keys': {}
        }
        
        # Get columns for each table
        for table in tables:
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table,))
            
            columns = {}
            for row in cursor.fetchall():
                columns[row['column_name']] = {
                    'type': row['data_type'],
                    'max_length': row['character_maximum_length'],
                    'nullable': row['is_nullable'],
                    'default': row['column_default']
                }
            
            schema_info['tables'][table] = columns
            
            # Get indexes for this table
            cursor.execute("""
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = %s
            """, (table,))
            
            indexes = {row['indexname']: row['indexdef'] for row in cursor.fetchall()}
            schema_info['indexes'][table] = indexes
            
            # Get foreign keys
            cursor.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
            """, (table,))
            
            fkeys = []
            for row in cursor.fetchall():
                fkeys.append({
                    'column': row['column_name'],
                    'references_table': row['foreign_table_name'],
                    'references_column': row['foreign_column_name']
                })
            
            if fkeys:
                schema_info['foreign_keys'][table] = fkeys
    
    return schema_info


def compare_schemas(local_schema: Dict, cloud_schema: Dict) -> Dict:
    """Compare two schemas and return differences."""
    differences = {
        'missing_tables_in_cloud': [],
        'missing_tables_in_local': [],
        'table_differences': {},
        'missing_indexes_in_cloud': {},
        'missing_foreign_keys_in_cloud': {}
    }
    
    local_tables = set(local_schema['tables'].keys())
    cloud_tables = set(cloud_schema['tables'].keys())
    
    # Find missing tables
    differences['missing_tables_in_cloud'] = sorted(local_tables - cloud_tables)
    differences['missing_tables_in_local'] = sorted(cloud_tables - local_tables)
    
    # Compare common tables
    common_tables = local_tables & cloud_tables
    
    for table in sorted(common_tables):
        local_cols = set(local_schema['tables'][table].keys())
        cloud_cols = set(cloud_schema['tables'][table].keys())
        
        missing_in_cloud = local_cols - cloud_cols
        missing_in_local = cloud_cols - local_cols
        
        # Check for type mismatches in common columns
        type_mismatches = []
        common_cols = local_cols & cloud_cols
        for col in common_cols:
            local_type = local_schema['tables'][table][col]['type']
            cloud_type = cloud_schema['tables'][table][col]['type']
            if local_type != cloud_type:
                type_mismatches.append({
                    'column': col,
                    'local_type': local_type,
                    'cloud_type': cloud_type
                })
        
        if missing_in_cloud or missing_in_local or type_mismatches:
            differences['table_differences'][table] = {
                'missing_columns_in_cloud': sorted(missing_in_cloud),
                'missing_columns_in_local': sorted(missing_in_local),
                'type_mismatches': type_mismatches
            }
        
        # Compare indexes
        local_indexes = set(local_schema['indexes'].get(table, {}).keys())
        cloud_indexes = set(cloud_schema['indexes'].get(table, {}).keys())
        missing_indexes = local_indexes - cloud_indexes
        
        if missing_indexes:
            differences['missing_indexes_in_cloud'][table] = sorted(missing_indexes)
    
    return differences


def print_comparison_report(differences: Dict):
    """Print a formatted comparison report."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}DATABASE SCHEMA COMPARISON REPORT{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Missing tables in cloud
    if differences['missing_tables_in_cloud']:
        print(f"{Colors.FAIL}{Colors.BOLD}❌ TABLES MISSING IN CLOUD:{Colors.ENDC}")
        for table in differences['missing_tables_in_cloud']:
            print(f"   • {table}")
        print()
    else:
        print(f"{Colors.OKGREEN}✅ No missing tables in cloud{Colors.ENDC}\n")
    
    # Extra tables in cloud
    if differences['missing_tables_in_local']:
        print(f"{Colors.WARNING}{Colors.BOLD}⚠️  EXTRA TABLES IN CLOUD (not in local):{Colors.ENDC}")
        for table in differences['missing_tables_in_local']:
            print(f"   • {table}")
        print()
    
    # Table differences
    if differences['table_differences']:
        print(f"{Colors.WARNING}{Colors.BOLD}⚠️  TABLE STRUCTURE DIFFERENCES:{Colors.ENDC}\n")
        for table, diffs in differences['table_differences'].items():
            print(f"{Colors.OKCYAN}Table: {table}{Colors.ENDC}")
            
            if diffs['missing_columns_in_cloud']:
                print(f"  {Colors.FAIL}Missing columns in cloud:{Colors.ENDC}")
                for col in diffs['missing_columns_in_cloud']:
                    print(f"    - {col}")
            
            if diffs['missing_columns_in_local']:
                print(f"  {Colors.WARNING}Extra columns in cloud:{Colors.ENDC}")
                for col in diffs['missing_columns_in_local']:
                    print(f"    + {col}")
            
            if diffs['type_mismatches']:
                print(f"  {Colors.WARNING}Type mismatches:{Colors.ENDC}")
                for mismatch in diffs['type_mismatches']:
                    print(f"    ~ {mismatch['column']}: {mismatch['local_type']} (local) vs {mismatch['cloud_type']} (cloud)")
            
            print()
    else:
        print(f"{Colors.OKGREEN}✅ All common tables have matching structures{Colors.ENDC}\n")
    
    # Missing indexes
    if differences['missing_indexes_in_cloud']:
        print(f"{Colors.WARNING}{Colors.BOLD}⚠️  MISSING INDEXES IN CLOUD:{Colors.ENDC}\n")
        for table, indexes in differences['missing_indexes_in_cloud'].items():
            print(f"  Table: {table}")
            for idx in indexes:
                print(f"    - {idx}")
        print()
    
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    # Summary
    issues = (
        len(differences['missing_tables_in_cloud']) +
        len(differences['table_differences']) +
        len(differences['missing_indexes_in_cloud'])
    )
    
    if issues == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✅ SCHEMAS ARE IDENTICAL{Colors.ENDC}\n")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}❌ FOUND {issues} SCHEMA DIFFERENCE(S){Colors.ENDC}")
        print(f"{Colors.WARNING}Run the migration script to fix cloud database{Colors.ENDC}\n")


def save_report_to_file(differences: Dict, filename: str = 'schema_comparison_report.json'):
    """Save comparison report to JSON file."""
    with open(filename, 'w') as f:
        json.dump(differences, f, indent=2, default=str)
    print(f"{Colors.OKGREEN}📄 Report saved to: {filename}{Colors.ENDC}")


def main():
    """Main comparison function."""
    print(f"\n{Colors.OKBLUE}Connecting to databases...{Colors.ENDC}\n")
    
    try:
        # Connect to local database
        print("📍 Connecting to LOCAL database...")
        local_conn = get_local_connection()
        print(f"{Colors.OKGREEN}✅ Connected to local database{Colors.ENDC}")
        
        # Connect to cloud database
        print("☁️  Connecting to CLOUD database...")
        cloud_conn = get_cloud_connection()
        print(f"{Colors.OKGREEN}✅ Connected to cloud database{Colors.ENDC}\n")
        
        # Extract schemas
        print("🔍 Analyzing LOCAL schema...")
        local_schema = get_schema_info(local_conn)
        print(f"   Found {len(local_schema['tables'])} tables\n")
        
        print("🔍 Analyzing CLOUD schema...")
        cloud_schema = get_schema_info(cloud_conn)
        print(f"   Found {len(cloud_schema['tables'])} tables\n")
        
        # Compare
        print("⚖️  Comparing schemas...\n")
        differences = compare_schemas(local_schema, cloud_schema)
        
        # Print report
        print_comparison_report(differences)
        
        # Save to file
        save_report_to_file(differences)
        
        # Close connections
        local_conn.close()
        cloud_conn.close()
        
        # Exit with appropriate code
        issues = (
            len(differences['missing_tables_in_cloud']) +
            len(differences['table_differences'])
        )
        sys.exit(0 if issues == 0 else 1)
        
    except psycopg2.Error as e:
        print(f"\n{Colors.FAIL}❌ Database connection error:{Colors.ENDC}")
        print(f"{Colors.FAIL}{str(e)}{Colors.ENDC}\n")
        print(f"{Colors.WARNING}Troubleshooting:{Colors.ENDC}")
        print(f"  • Local DB: Ensure PostgreSQL is running on localhost:5433")
        print(f"  • Cloud DB: Ensure Cloud SQL Proxy is running or use Cloud Shell")
        print(f"  • Set CLOUD_DB_PASSWORD environment variable for cloud connection\n")
        sys.exit(2)
    
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Unexpected error:{Colors.ENDC}")
        print(f"{Colors.FAIL}{str(e)}{Colors.ENDC}\n")
        sys.exit(3)


if __name__ == '__main__':
    main()
