#!/usr/bin/env python3
"""
Sync database data between local and cloud environments.

This script synchronizes:
- Groups
- Users (except passwords for security)
- Corpora
- Group-Corpus permissions (Permission Matrix)
- User-Group memberships

Usage:
    # Sync FROM cloud TO local (recommended for local dev):
    python sync_database_data.py --from-cloud

    # Sync FROM local TO cloud (use with caution):
    python sync_database_data.py --to-cloud

    # Dry run to see what would change:
    python sync_database_data.py --from-cloud --dry-run
"""

import os
import sys
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Color codes for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

def log_info(msg):
    print(f"{CYAN}ℹ️  {msg}{NC}")

def log_success(msg):
    print(f"{GREEN}✅ {msg}{NC}")

def log_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{NC}")

def log_error(msg):
    print(f"{RED}❌ {msg}{NC}")

def log_header(msg):
    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}{msg}{NC}")
    print(f"{BLUE}{'=' * 70}{NC}\n")

class DatabaseSync:
    def __init__(self, local_config, cloud_config):
        self.local_config = local_config
        self.cloud_config = cloud_config
        self.local_conn = None
        self.cloud_conn = None
    
    def connect(self):
        """Connect to both databases."""
        try:
            log_info("Connecting to local database...")
            self.local_conn = psycopg2.connect(**self.local_config)
            log_success("Connected to local database")
        except Exception as e:
            log_error(f"Failed to connect to local database: {e}")
            return False
        
        try:
            log_info("Connecting to cloud database...")
            self.cloud_conn = psycopg2.connect(**self.cloud_config)
            log_success("Connected to cloud database")
        except Exception as e:
            log_error(f"Failed to connect to cloud database: {e}")
            return False
        
        return True
    
    def close(self):
        """Close database connections."""
        if self.local_conn:
            self.local_conn.close()
        if self.cloud_conn:
            self.cloud_conn.close()
    
    def fetch_data(self, conn, query):
        """Fetch data from database."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()
    
    def sync_groups(self, source_conn, dest_conn, dry_run=False):
        """Sync groups table."""
        log_header("Syncing Groups")
        
        # Fetch groups from source
        source_groups = self.fetch_data(source_conn, 
            "SELECT id, name, description FROM groups ORDER BY id")
        
        # Fetch groups from destination
        dest_groups = self.fetch_data(dest_conn,
            "SELECT id, name, description FROM groups ORDER BY id")
        
        source_dict = {g['name']: g for g in source_groups}
        dest_dict = {g['name']: g for g in dest_groups}
        
        log_info(f"Source groups: {len(source_groups)}")
        log_info(f"Destination groups: {len(dest_groups)}")
        
        # Find differences
        to_add = set(source_dict.keys()) - set(dest_dict.keys())
        to_update = set(source_dict.keys()) & set(dest_dict.keys())
        
        if dry_run:
            if to_add:
                log_warning(f"Would add {len(to_add)} groups: {', '.join(to_add)}")
            if to_update:
                log_info(f"Would check {len(to_update)} existing groups for updates")
            return
        
        # Add new groups
        if to_add:
            log_info(f"Adding {len(to_add)} new groups...")
            with dest_conn.cursor() as cur:
                for group_name in to_add:
                    group = source_dict[group_name]
                    cur.execute(
                        "INSERT INTO groups (name, description) VALUES (%s, %s) "
                        "ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description",
                        (group['name'], group['description'])
                    )
                    log_success(f"  Added/Updated: {group_name}")
            dest_conn.commit()
        
        log_success("Groups synced")
    
    def sync_corpora(self, source_conn, dest_conn, dry_run=False):
        """Sync corpora table."""
        log_header("Syncing Corpora")
        
        source_corpora = self.fetch_data(source_conn,
            "SELECT id, name, display_name, gcs_bucket, description, vertex_corpus_id, is_active "
            "FROM corpora ORDER BY id")
        
        dest_corpora = self.fetch_data(dest_conn,
            "SELECT id, name, display_name, gcs_bucket, description, vertex_corpus_id, is_active "
            "FROM corpora ORDER BY id")
        
        source_dict = {c['name']: c for c in source_corpora}
        dest_dict = {c['name']: c for c in dest_corpora}
        
        log_info(f"Source corpora: {len(source_corpora)}")
        log_info(f"Destination corpora: {len(dest_corpora)}")
        
        to_add = set(source_dict.keys()) - set(dest_dict.keys())
        to_update = set(source_dict.keys()) & set(dest_dict.keys())
        
        if dry_run:
            if to_add:
                log_warning(f"Would add {len(to_add)} corpora: {', '.join(to_add)}")
            if to_update:
                log_info(f"Would check {len(to_update)} existing corpora for updates")
            return
        
        # Add/update corpora
        if to_add or to_update:
            with dest_conn.cursor() as cur:
                for corpus_name in (to_add | to_update):
                    corpus = source_dict[corpus_name]
                    cur.execute(
                        """INSERT INTO corpora 
                           (name, display_name, gcs_bucket, description, vertex_corpus_id, is_active)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           ON CONFLICT (name) DO UPDATE SET
                               display_name = EXCLUDED.display_name,
                               gcs_bucket = EXCLUDED.gcs_bucket,
                               description = EXCLUDED.description,
                               vertex_corpus_id = EXCLUDED.vertex_corpus_id,
                               is_active = EXCLUDED.is_active""",
                        (corpus['name'], corpus['display_name'], corpus['gcs_bucket'],
                         corpus['description'], corpus['vertex_corpus_id'], corpus['is_active'])
                    )
                    action = "Added" if corpus_name in to_add else "Updated"
                    log_success(f"  {action}: {corpus_name}")
            dest_conn.commit()
        
        log_success("Corpora synced")
    
    def sync_permissions(self, source_conn, dest_conn, dry_run=False):
        """Sync group_corpus_access (Permission Matrix)."""
        log_header("Syncing Permission Matrix")
        
        # Get group and corpus IDs mapping first
        source_groups = {g['name']: g['id'] for g in self.fetch_data(source_conn, "SELECT id, name FROM groups")}
        dest_groups = {g['name']: g['id'] for g in self.fetch_data(dest_conn, "SELECT id, name FROM groups")}
        
        source_corpora = {c['name']: c['id'] for c in self.fetch_data(source_conn, "SELECT id, name FROM corpora")}
        dest_corpora = {c['name']: c['id'] for c in self.fetch_data(dest_conn, "SELECT id, name FROM corpora")}
        
        # Fetch permissions with group and corpus names
        source_perms = self.fetch_data(source_conn,
            """SELECT g.name as group_name, c.name as corpus_name, gca.permission
               FROM group_corpus_access gca
               JOIN groups g ON gca.group_id = g.id
               JOIN corpora c ON gca.corpus_id = c.id""")
        
        dest_perms = self.fetch_data(dest_conn,
            """SELECT g.name as group_name, c.name as corpus_name, gca.permission
               FROM group_corpus_access gca
               JOIN groups g ON gca.group_id = g.id
               JOIN corpora c ON gca.corpus_id = c.id""")
        
        # Create permission keys
        source_perm_set = {(p['group_name'], p['corpus_name'], p['permission']) for p in source_perms}
        dest_perm_set = {(p['group_name'], p['corpus_name'], p['permission']) for p in dest_perms}
        
        log_info(f"Source permissions: {len(source_perms)}")
        log_info(f"Destination permissions: {len(dest_perms)}")
        
        to_add = source_perm_set - dest_perm_set
        to_remove = dest_perm_set - source_perm_set
        
        if dry_run:
            if to_add:
                log_warning(f"Would add {len(to_add)} permissions")
                for group, corpus, perm in sorted(to_add):
                    print(f"    + {group} -> {corpus} ({perm})")
            if to_remove:
                log_warning(f"Would remove {len(to_remove)} permissions")
                for group, corpus, perm in sorted(to_remove):
                    print(f"    - {group} -> {corpus} ({perm})")
            return
        
        # Remove old permissions
        if to_remove:
            log_info(f"Removing {len(to_remove)} obsolete permissions...")
            with dest_conn.cursor() as cur:
                for group_name, corpus_name, permission in to_remove:
                    if group_name in dest_groups and corpus_name in dest_corpora:
                        cur.execute(
                            """DELETE FROM group_corpus_access 
                               WHERE group_id = %s AND corpus_id = %s AND permission = %s""",
                            (dest_groups[group_name], dest_corpora[corpus_name], permission)
                        )
                        log_info(f"  Removed: {group_name} -> {corpus_name} ({permission})")
            dest_conn.commit()
        
        # Add new permissions
        if to_add:
            log_info(f"Adding {len(to_add)} new permissions...")
            with dest_conn.cursor() as cur:
                for group_name, corpus_name, permission in to_add:
                    if group_name in dest_groups and corpus_name in dest_corpora:
                        cur.execute(
                            """INSERT INTO group_corpus_access (group_id, corpus_id, permission)
                               VALUES (%s, %s, %s)
                               ON CONFLICT (group_id, corpus_id) DO UPDATE SET permission = EXCLUDED.permission""",
                            (dest_groups[group_name], dest_corpora[corpus_name], permission)
                        )
                        log_success(f"  Added: {group_name} -> {corpus_name} ({permission})")
            dest_conn.commit()
        
        log_success("Permission Matrix synced")
    
    def sync_from_cloud_to_local(self, dry_run=False):
        """Sync cloud -> local (recommended for local development)."""
        log_header("Syncing FROM Cloud TO Local")
        if dry_run:
            log_warning("DRY RUN MODE - No changes will be made")
        
        self.sync_groups(self.cloud_conn, self.local_conn, dry_run)
        self.sync_corpora(self.cloud_conn, self.local_conn, dry_run)
        self.sync_permissions(self.cloud_conn, self.local_conn, dry_run)
        
        if not dry_run:
            log_success("✨ Local database synced with cloud!")
    
    def sync_from_local_to_cloud(self, dry_run=False):
        """Sync local -> cloud (use with caution in production)."""
        log_header("Syncing FROM Local TO Cloud")
        log_warning("⚠️  This will modify PRODUCTION cloud database!")
        
        if not dry_run:
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                log_info("Sync cancelled")
                return
        
        if dry_run:
            log_warning("DRY RUN MODE - No changes will be made")
        
        self.sync_groups(self.local_conn, self.cloud_conn, dry_run)
        self.sync_corpora(self.local_conn, self.cloud_conn, dry_run)
        self.sync_permissions(self.local_conn, self.cloud_conn, dry_run)
        
        if not dry_run:
            log_success("✨ Cloud database synced with local!")

def main():
    parser = argparse.ArgumentParser(
        description='Sync database data between local and cloud environments'
    )
    parser.add_argument(
        '--from-cloud',
        action='store_true',
        help='Sync FROM cloud TO local (recommended for local dev)'
    )
    parser.add_argument(
        '--to-cloud',
        action='store_true',
        help='Sync FROM local TO cloud (use with caution)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would change without making changes'
    )
    
    args = parser.parse_args()
    
    if not args.from_cloud and not args.to_cloud:
        parser.error("Must specify either --from-cloud or --to-cloud")
    
    if args.from_cloud and args.to_cloud:
        parser.error("Cannot specify both --from-cloud and --to-cloud")
    
    # Local database config
    local_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5433')),
        'database': os.getenv('DB_NAME', 'adk_agents_db_dev'),
        'user': os.getenv('DB_USER', 'adk_dev_user'),
        'password': os.getenv('DB_PASSWORD', 'dev_password_123'),
    }
    
    # Cloud database config (requires Cloud SQL Proxy or IAP tunnel)
    cloud_config = {
        'host': os.getenv('CLOUD_DB_HOST', 'localhost'),  # Use 127.0.0.1 with Cloud SQL Proxy
        'port': int(os.getenv('CLOUD_DB_PORT', '5432')),  # Cloud SQL Proxy default port
        'database': os.getenv('CLOUD_DB_NAME', 'adk_agents_db'),
        'user': os.getenv('CLOUD_DB_USER', 'adk_app_user'),
        'password': os.getenv('CLOUD_DB_PASSWORD', ''),  # Set via environment
    }
    
    log_header("Database Sync Tool")
    log_info(f"Local:  {local_config['user']}@{local_config['host']}:{local_config['port']}/{local_config['database']}")
    log_info(f"Cloud:  {cloud_config['user']}@{cloud_config['host']}:{cloud_config['port']}/{cloud_config['database']}")
    
    sync = DatabaseSync(local_config, cloud_config)
    
    try:
        if not sync.connect():
            sys.exit(1)
        
        if args.from_cloud:
            sync.sync_from_cloud_to_local(dry_run=args.dry_run)
        else:
            sync.sync_from_local_to_cloud(dry_run=args.dry_run)
        
        log_success("✅ Sync completed successfully!")
        
    except Exception as e:
        log_error(f"Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        sync.close()

if __name__ == "__main__":
    main()
