#!/usr/bin/env python3
"""
Direct Database Backup Script
Creates a SQL dump using direct database connection
Usage: python backup_database_direct.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import gzip

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.connection import get_db_connection

def get_table_schema(cursor, table_name):
    """Get CREATE TABLE statement for a table."""
    cursor.execute("""
        SELECT 
            'CREATE TABLE ' || quote_ident(table_name) || ' (' ||
            string_agg(
                quote_ident(column_name) || ' ' || 
                data_type ||
                CASE 
                    WHEN character_maximum_length IS NOT NULL 
                    THEN '(' || character_maximum_length || ')'
                    ELSE ''
                END ||
                CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END ||
                CASE WHEN column_default IS NOT NULL THEN ' DEFAULT ' || column_default ELSE '' END,
                ', '
            ) || ');'
        FROM information_schema.columns
        WHERE table_name = %s
        GROUP BY table_name;
    """, (table_name,))
    result = cursor.fetchone()
    return result['?column?'] if result else None

def backup_database():
    """Create a complete database backup."""
    
    backup_dir = Path(__file__).parent / 'database_backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_direct_{timestamp}.sql"
    
    print("=" * 60)
    print("PostgreSQL Database Backup (Direct Connection)")
    print("=" * 60)
    print(f"Timestamp: {timestamp}")
    print(f"Backup file: {backup_file}")
    print()
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            
            print(f"Found {len(tables)} tables to backup")
            print()
            
            with open(backup_file, 'w') as f:
                # Write header
                f.write(f"-- PostgreSQL Database Backup\n")
                f.write(f"-- Created: {datetime.now().isoformat()}\n")
                f.write(f"-- Tables: {len(tables)}\n")
                f.write(f"\n")
                f.write(f"SET client_encoding = 'UTF8';\n")
                f.write(f"SET standard_conforming_strings = on;\n")
                f.write(f"\n")
                
                # Backup each table
                for table_name in tables:
                    print(f"Backing up table: {table_name}")
                    
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                    row_count = cursor.fetchone()['count']
                    
                    f.write(f"\n-- Table: {table_name} ({row_count} rows)\n")
                    f.write(f"-- ============================================\n\n")
                    
                    # Get all data
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    
                    if rows:
                        # Get column names
                        columns = list(rows[0].keys())
                        
                        # Write INSERT statements in batches
                        batch_size = 100
                        for i in range(0, len(rows), batch_size):
                            batch = rows[i:i + batch_size]
                            
                            for row in batch:
                                values = []
                                for col in columns:
                                    val = row[col]
                                    if val is None:
                                        values.append('NULL')
                                    elif isinstance(val, bool):
                                        values.append('TRUE' if val else 'FALSE')
                                    elif isinstance(val, (int, float)):
                                        values.append(str(val))
                                    else:
                                        # Escape single quotes
                                        val_str = str(val).replace("'", "''")
                                        values.append(f"'{val_str}'")
                                
                                cols_str = ', '.join(columns)
                                vals_str = ', '.join(values)
                                f.write(f"INSERT INTO {table_name} ({cols_str}) VALUES ({vals_str});\n")
                    
                    f.write(f"\n")
                
                # Get sequences
                cursor.execute("""
                    SELECT sequence_name, last_value 
                    FROM information_schema.sequences s
                    JOIN pg_sequences ps ON s.sequence_name = ps.sequencename
                    WHERE s.sequence_schema = 'public';
                """)
                sequences = cursor.fetchall()
                
                if sequences:
                    f.write(f"\n-- Sequences\n")
                    f.write(f"-- ============================================\n\n")
                    for seq in sequences:
                        f.write(f"SELECT setval('{seq['sequence_name']}', {seq['last_value']}, true);\n")
        
        print()
        print("✅ Backup created successfully")
        
        # Compress backup
        print("Compressing backup...")
        with open(backup_file, 'rb') as f_in:
            with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                f_out.writelines(f_in)
        
        # Remove uncompressed file
        backup_file.unlink()
        backup_compressed = f"{backup_file}.gz"
        
        print("✅ Backup compressed successfully")
        
        # Display info
        backup_size = os.path.getsize(backup_compressed)
        backup_size_mb = backup_size / (1024 * 1024)
        
        print()
        print("=" * 60)
        print("Backup Complete")
        print("=" * 60)
        print(f"Backup file: {backup_compressed}")
        print(f"Backup size: {backup_size_mb:.2f} MB")
        print()
        
        # List recent backups
        print("Recent backups:")
        backups = sorted(backup_dir.glob("backup_*.sql.gz"), 
                        key=lambda x: x.stat().st_mtime, 
                        reverse=True)[:5]
        
        for backup in backups:
            size_mb = backup.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"  {backup.name} ({size_mb:.2f} MB) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = backup_database()
    sys.exit(0 if success else 1)
