#!/usr/bin/env python3
"""
Database Schema and Data Documentation Script
Creates a comprehensive backup of database schema and data structure
This works even when pg_dump is not available
Usage: python backup_database_schema.py
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def backup_schema_info():
    """Create a detailed backup of database schema information."""
    
    backup_dir = Path(__file__).parent / 'database_backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"schema_backup_{timestamp}.json"
    
    print("=" * 60)
    print("Database Schema Backup")
    print("=" * 60)
    print(f"Timestamp: {timestamp}")
    print()
    
    try:
        # Import here to avoid connection issues at module level
        from database.connection import get_db_connection, PG_CONFIG
        
        print(f"Database: {PG_CONFIG.get('database', 'N/A')}")
        print(f"Host: {PG_CONFIG.get('host', 'N/A')}")
        print()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            backup_data = {
                'timestamp': timestamp,
                'database': PG_CONFIG.get('database'),
                'tables': {},
                'sequences': [],
                'indexes': [],
                'foreign_keys': []
            }
            
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            
            print(f"Found {len(tables)} tables")
            print()
            
            # Backup each table structure and data count
            for table_name in tables:
                print(f"Processing: {table_name}")
                
                # Get columns
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                columns = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                row_count = cursor.fetchone()['count']
                
                # Get sample data (first 5 rows)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_data = cursor.fetchall()
                
                backup_data['tables'][table_name] = {
                    'columns': columns,
                    'row_count': row_count,
                    'sample_data': sample_data
                }
            
            # Get sequences
            cursor.execute("""
                SELECT 
                    sequence_name,
                    start_value,
                    minimum_value,
                    maximum_value,
                    increment
                FROM information_schema.sequences
                WHERE sequence_schema = 'public';
            """)
            backup_data['sequences'] = cursor.fetchall()
            
            # Get indexes
            cursor.execute("""
                SELECT
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
            backup_data['indexes'] = cursor.fetchall()
            
            # Get foreign keys
            cursor.execute("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    tc.constraint_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_name;
            """)
            backup_data['foreign_keys'] = cursor.fetchall()
            
            # Write backup file
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            print()
            print("✅ Schema backup created successfully")
            
            # Display summary
            print()
            print("=" * 60)
            print("Backup Summary")
            print("=" * 60)
            print(f"Backup file: {backup_file}")
            print(f"Tables: {len(tables)}")
            print(f"Total rows: {sum(t['row_count'] for t in backup_data['tables'].values())}")
            print(f"Sequences: {len(backup_data['sequences'])}")
            print(f"Indexes: {len(backup_data['indexes'])}")
            print(f"Foreign keys: {len(backup_data['foreign_keys'])}")
            print()
            
            # Show tables with row counts
            print("Tables and row counts:")
            for table_name, table_info in sorted(backup_data['tables'].items()):
                print(f"  {table_name}: {table_info['row_count']} rows")
            
            print()
            print(f"✅ Backup saved to: {backup_file}")
            print()
            
            return True
            
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = backup_schema_info()
    sys.exit(0 if success else 1)
