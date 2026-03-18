#!/usr/bin/env python3
"""
Database Backup Script for PostgreSQL
Creates a full backup of the database before schema migration
Usage: python backup_database.py
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.connection import PG_CONFIG

def create_backup():
    """Create a PostgreSQL database backup."""
    
    # Backup configuration
    backup_dir = Path(__file__).parent / 'database_backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = PG_CONFIG['database']
    backup_file = backup_dir / f"backup_{db_name}_{timestamp}.sql"
    backup_compressed = f"{backup_file}.gz"
    
    print("=" * 60)
    print("PostgreSQL Database Backup")
    print("=" * 60)
    print(f"Database: {db_name}")
    print(f"Host: {PG_CONFIG['host']}")
    print(f"User: {PG_CONFIG['user']}")
    print(f"Timestamp: {timestamp}")
    print()
    
    # Check if pg_dump is available
    try:
        subprocess.run(['pg_dump', '--version'], 
                      capture_output=True, 
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: pg_dump command not found")
        print("Please install PostgreSQL client tools")
        return False
    
    # Build pg_dump command
    cmd = ['pg_dump']
    
    # Handle Cloud SQL Unix socket connection
    if PG_CONFIG['host'].startswith('/cloudsql/'):
        print("Using Cloud SQL Unix socket connection")
        cmd.extend(['-h', PG_CONFIG['host']])
    else:
        # Standard TCP connection
        cmd.extend(['-h', PG_CONFIG['host']])
        if 'port' in PG_CONFIG:
            cmd.extend(['-p', str(PG_CONFIG['port'])])
    
    cmd.extend([
        '-U', PG_CONFIG['user'],
        '-d', PG_CONFIG['database'],
        '--format=plain',
        '--no-owner',
        '--no-acl',
        '--verbose',
        '-f', str(backup_file)
    ])
    
    # Set password environment variable if available
    env = os.environ.copy()
    if PG_CONFIG.get('password'):
        env['PGPASSWORD'] = PG_CONFIG['password']
    
    print("Creating backup...")
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✅ Backup created successfully")
        
        # Compress backup
        print("Compressing backup...")
        subprocess.run(
            ['gzip', str(backup_file)],
            check=True
        )
        
        print("✅ Backup compressed successfully")
        
        # Display backup info
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
        
        # Create symlink to latest backup
        latest_link = backup_dir / 'latest_backup.sql.gz'
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(Path(backup_compressed).name)
        
        print()
        print(f"✅ Latest backup symlink: {latest_link}")
        print()
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Backup failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = create_backup()
    sys.exit(0 if success else 1)
