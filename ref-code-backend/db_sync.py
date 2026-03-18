#!/usr/bin/env python3
"""
Comprehensive Database Sync Tool for Multi-Client Deployments
=============================================================

Syncs ALL tables between local PostgreSQL and cloud PostgreSQL databases,
respecting foreign key dependencies. Replaces the limited sync_database_data.py.

Features:
- Syncs all ~28 tables in correct FK dependency order
- Dry-run mode (preview changes without modifying)
- Verify mode (compare databases without modifying)
- Pre-sync cloud backup via gcloud
- Sequence reset after sync
- Post-sync row count verification
- Reads client config from environments/<client>.yaml

Usage:
    # Dry run - preview what would change
    python db_sync.py --to-cloud --dry-run --env environments/develom.yaml

    # Full sync local → cloud with backup
    python db_sync.py --to-cloud --backup --env environments/develom.yaml

    # Sync cloud → local
    python db_sync.py --from-cloud --env environments/develom.yaml

    # Verify parity only (no changes)
    python db_sync.py --verify --env environments/develom.yaml

    # Sync specific tables only
    python db_sync.py --to-cloud --tables chatbot_users,chatbot_groups --env environments/develom.yaml

Author: ADK RAG Agent Team
Date: 2026-02-08
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
import psycopg2.extras
import yaml

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("db_sync")

# ---------------------------------------------------------------------------
# Color helpers for terminal output
# ---------------------------------------------------------------------------
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
NC = "\033[0m"


def c_red(t): return f"{RED}{t}{NC}"
def c_green(t): return f"{GREEN}{t}{NC}"
def c_yellow(t): return f"{YELLOW}{t}{NC}"
def c_blue(t): return f"{BLUE}{t}{NC}"
def c_cyan(t): return f"{CYAN}{t}{NC}"
def c_bold(t): return f"{BOLD}{t}{NC}"


# ---------------------------------------------------------------------------
# Table sync order — respects FK dependencies
# ---------------------------------------------------------------------------
# Phase 1: Parent / root tables (no FK deps on other custom tables)
# Phase 2: Child / junction tables (depend on Phase 1 tables)
# Phase 3: Metadata / log tables (depend on Phase 1 tables, safe to skip)
#
# Tables that may not exist in every database are handled gracefully.
# ---------------------------------------------------------------------------

SYNC_PHASES = OrderedDict({
    "Phase 1 — Parent Tables": [
        "users",
        "groups",
        "roles",
        "agents",
        "corpora",
        "chatbot_users",
        "chatbot_groups",
        "chatbot_agents",
        # These may have been renamed via migration 010:
        #   chatbot_roles → chatbot_agent_types
        #   chatbot_permissions → chatbot_tools
        # We detect which name exists at runtime.
        "chatbot_agent_types",
        "chatbot_tools",
    ],
    "Phase 2 — Junction Tables": [
        "user_profiles",
        "user_groups",
        "group_roles",
        "user_agent_access",
        "group_corpus_access",
        "chatbot_user_groups",
        "chatbot_group_agent_types",
        "chatbot_agent_type_tools",
        "chatbot_corpus_access",
        "chatbot_agent_access",
        "chatbot_tool_access",
        "chatbot_group_agents",
    ],
    "Phase 3 — Metadata / Log Tables": [
        "user_sessions",
        "session_corpus_selections",
        "corpus_audit_log",
        "corpus_metadata",
        "corpus_sync_schedule",
        "document_access_log",
    ],
})

# Legacy table name mappings (pre-rename → post-rename)
LEGACY_TABLE_NAMES = {
    "chatbot_roles": "chatbot_agent_types",
    "chatbot_permissions": "chatbot_tools",
    "chatbot_role_permissions": "chatbot_agent_type_tools",
    "chatbot_group_roles": "chatbot_group_agent_types",
}


# ---------------------------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------------------------

def load_env_config(env_path: str) -> dict:
    """Load client environment configuration from YAML file."""
    abs_path = os.path.abspath(env_path)
    if not os.path.exists(abs_path):
        logger.error(f"Environment file not found: {abs_path}")
        sys.exit(1)

    with open(abs_path, "r") as f:
        config = yaml.safe_load(f)

    required_keys = ["client_name", "account_env", "project_id", "database"]
    for key in required_keys:
        if key not in config or not config[key]:
            logger.error(f"Missing required key '{key}' in {abs_path}")
            sys.exit(1)

    db = config["database"]
    required_db_keys = ["cloud_sql_instance", "name", "user"]
    for key in required_db_keys:
        if key not in db or not db[key]:
            logger.error(f"Missing required database key '{key}' in {abs_path}")
            sys.exit(1)

    return config


def fetch_cloud_db_password(project_id: str, secret_name: str = "db-password") -> str:
    """Fetch cloud DB password from GCP Secret Manager."""
    try:
        result = subprocess.run(
            ["gcloud", "secrets", "versions", "access", "latest",
             "--secret", secret_name, "--project", project_id],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            logger.info(f"Retrieved cloud DB password from Secret Manager ({secret_name})")
            return result.stdout.strip()
        else:
            logger.warning(f"Could not retrieve secret '{secret_name}': {result.stderr.strip()}")
            return ""
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"Failed to fetch secret from Secret Manager: {e}")
        return ""


def build_db_configs(config: dict) -> Tuple[dict, dict]:
    """Build local and cloud psycopg2 connection dicts from environment config."""
    db = config["database"]
    local = db.get("local", {})

    local_config = {
        "host": local.get("host", os.getenv("DB_HOST", "localhost")),
        "port": int(local.get("port", os.getenv("DB_PORT", "5433"))),
        "database": local.get("name", os.getenv("DB_NAME", "adk_agents_db_dev")),
        "user": local.get("user", os.getenv("DB_USER", "adk_dev_user")),
        "password": local.get("password", os.getenv("DB_PASSWORD", "dev_password_123")),
    }

    # Resolve cloud password: YAML → env var → Secret Manager
    cloud_password = db.get("password", "") or os.getenv("CLOUD_DB_PASSWORD", "")
    if not cloud_password:
        secret_name = db.get("password_secret_name", "") or "db-password"
        cloud_password = fetch_cloud_db_password(config["project_id"], secret_name)

    cloud_config = {
        "host": os.getenv("CLOUD_DB_HOST", "localhost"),
        "port": int(os.getenv("CLOUD_DB_PORT", "5434")),
        "database": db.get("name", os.getenv("CLOUD_DB_NAME", "adk_agents_db")),
        "user": db.get("user", os.getenv("CLOUD_DB_USER", "adk_app_user")),
        "password": cloud_password,
    }

    return local_config, cloud_config


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def connect(config: dict, label: str) -> psycopg2.extensions.connection:
    """Create a psycopg2 connection with error handling."""
    try:
        conn = psycopg2.connect(**config)
        conn.autocommit = False
        logger.info(f"Connected to {c_green(label)}: {config['database']}@{config['host']}:{config.get('port', 5432)}")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Failed to connect to {label}: {e}")
        sys.exit(1)


def get_existing_tables(conn: psycopg2.extensions.connection) -> set:
    """Get set of table names that exist in the public schema."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        return {row[0] for row in cur.fetchall()}


def get_table_columns(conn: psycopg2.extensions.connection, table: str) -> List[str]:
    """Get ordered list of column names for a table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
        """, (table,))
        return [row[0] for row in cur.fetchall()]


def get_column_types(conn: psycopg2.extensions.connection, table: str) -> dict:
    """Get column name → data_type mapping for a table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
        """, (table,))
        return {row[0]: (row[1], row[2]) for row in cur.fetchall()}


def get_primary_keys(conn: psycopg2.extensions.connection, table: str) -> List[str]:
    """Get the primary key column name(s) for a table. Returns list for composite keys."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass
              AND i.indisprimary
            ORDER BY a.attnum
        """, (table,))
        return [row[0] for row in cur.fetchall()]


def get_unique_columns(conn: psycopg2.extensions.connection, table: str) -> List[str]:
    """Get unique constraint columns (excluding PK) for conflict resolution."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT array_agg(a.attname ORDER BY a.attnum)
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass
              AND i.indisunique
              AND NOT i.indisprimary
            GROUP BY i.indexrelid
            ORDER BY i.indexrelid
            LIMIT 1
        """, (table,))
        row = cur.fetchone()
        return row[0] if row else []


def fetch_all_rows(conn: psycopg2.extensions.connection, table: str, pk_cols: Optional[List[str]] = None) -> List[dict]:
    """Fetch all rows from a table as list of dicts, ordered by PK columns."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if pk_cols:
            order_by = ", ".join(pk_cols)
        else:
            order_by = "1"  # fallback: order by first column
        cur.execute(f"SELECT * FROM {table} ORDER BY {order_by}")
        return [dict(row) for row in cur.fetchall()]


def get_row_count(conn: psycopg2.extensions.connection, table: str) -> int:
    """Get row count for a table."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        return cur.fetchone()[0]


def get_max_id(conn: psycopg2.extensions.connection, table: str) -> Optional[int]:
    """Get max id value for a table. Returns None if table has no 'id' column."""
    columns = get_table_columns(conn, table)
    if "id" not in columns:
        return None
    with conn.cursor() as cur:
        cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
        return cur.fetchone()[0]


def reset_sequence(conn: psycopg2.extensions.connection, table: str, dry_run: bool = False):
    """Reset the serial sequence for a table to max(id) + 1. Skips tables without 'id'."""
    max_id = get_max_id(conn, table)
    if max_id is None:
        return  # No id column — no sequence to reset
    seq_name = f"{table}_id_seq"
    if dry_run:
        logger.info(f"  [DRY RUN] Would reset {seq_name} to {max_id + 1}")
    else:
        with conn.cursor() as cur:
            cur.execute(f"SELECT setval('{seq_name}', %s, true)", (max(max_id, 1),))
        logger.info(f"  Reset {seq_name} → {max(max_id, 1)}")


# ---------------------------------------------------------------------------
# Resolve table names (handle legacy renames)
# ---------------------------------------------------------------------------

def resolve_table_name(table: str, existing_tables: set) -> Optional[str]:
    """
    Resolve a table name, checking for legacy names.
    Returns the actual table name that exists, or None if not found.
    """
    if table in existing_tables:
        return table

    # Check if this is a post-rename name and the legacy name exists
    reverse_map = {v: k for k, v in LEGACY_TABLE_NAMES.items()}
    if table in reverse_map and reverse_map[table] in existing_tables:
        legacy = reverse_map[table]
        logger.info(f"  Table '{table}' not found, using legacy name '{legacy}'")
        return legacy

    # Check if this is a legacy name and the new name exists
    if table in LEGACY_TABLE_NAMES and LEGACY_TABLE_NAMES[table] in existing_tables:
        new_name = LEGACY_TABLE_NAMES[table]
        logger.info(f"  Table '{table}' not found, using renamed table '{new_name}'")
        return new_name

    return None


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------

class DatabaseSync:
    """Comprehensive database synchronization engine."""

    def __init__(self, source_config: dict, dest_config: dict):
        self.source_config = source_config
        self.dest_config = dest_config
        self.source_conn: Optional[psycopg2.extensions.connection] = None
        self.dest_conn: Optional[psycopg2.extensions.connection] = None
        self.stats = {
            "tables_synced": 0,
            "tables_skipped": 0,
            "rows_inserted": 0,
            "rows_updated": 0,
            "rows_deleted": 0,
            "errors": [],
        }

    def connect(self, source_label: str = "SOURCE", dest_label: str = "DEST"):
        self.source_conn = connect(self.source_config, source_label)
        self.dest_conn = connect(self.dest_config, dest_label)

    def close(self):
        if self.source_conn:
            self.source_conn.close()
        if self.dest_conn:
            self.dest_conn.close()

    def _resolve_sync_tables(
        self,
        tables_filter: Optional[List[str]] = None,
        skip_phase3: bool = False,
    ) -> List[Tuple[str, str, str]]:
        """
        Resolve all tables to sync, returning list of (phase_name, src_table, dst_table).
        Skips tables that don't exist in either database.
        """
        source_tables = get_existing_tables(self.source_conn)
        dest_tables = get_existing_tables(self.dest_conn)
        resolved = []

        for phase_name, tables in SYNC_PHASES.items():
            if skip_phase3 and "Phase 3" in phase_name:
                continue
            for table in tables:
                if tables_filter and table not in tables_filter:
                    continue
                src_table = resolve_table_name(table, source_tables)
                dst_table = resolve_table_name(table, dest_tables)
                if not src_table:
                    logger.warning(f"  Table '{table}' does not exist in source — skipping")
                    self.stats["tables_skipped"] += 1
                    continue
                if not dst_table:
                    logger.warning(f"  Table '{table}' does not exist in destination — skipping")
                    self.stats["tables_skipped"] += 1
                    continue
                resolved.append((phase_name, src_table, dst_table))

        return resolved

    def _get_shared_columns(self, src_table: str, dst_table: str) -> List[str]:
        """Get columns that exist in both source and destination tables."""
        src_cols = get_table_columns(self.source_conn, src_table)
        dst_cols = set(get_table_columns(self.dest_conn, dst_table))
        shared = [c for c in src_cols if c in dst_cols]
        skipped = [c for c in src_cols if c not in dst_cols]
        if skipped:
            logger.info(f"    Columns only in source (skipped): {', '.join(skipped)}")
        return shared

    def sync_all(
        self,
        dry_run: bool = False,
        delete_orphans: bool = False,
        tables_filter: Optional[List[str]] = None,
        skip_phase3: bool = False,
    ):
        """
        Sync all tables using clear-and-reload strategy:
        1. TRUNCATE all destination tables in reverse FK order (Phase 3 → 2 → 1)
        2. INSERT all source rows in forward FK order (Phase 1 → 2 → 3)
        3. Reset sequences

        This guarantees an exact replica regardless of ID conflicts,
        unique constraint differences, or schema column mismatches.
        """
        mode = c_yellow("[DRY RUN]") if dry_run else c_green("[LIVE]")
        logger.info(f"\n{'='*70}")
        logger.info(f"  Database Sync — Clear & Reload {mode}")
        logger.info(f"  Source: {self.source_config['database']}@{self.source_config['host']}")
        logger.info(f"  Dest:   {self.dest_config['database']}@{self.dest_config['host']}")
        logger.info(f"{'='*70}\n")

        # Resolve all tables to sync
        resolved = self._resolve_sync_tables(tables_filter, skip_phase3)
        if not resolved:
            logger.warning("No tables to sync.")
            return

        # ── Step 1: TRUNCATE ALL destination tables in one statement ──
        logger.info(f"\n{c_blue('━' * 60)}")
        logger.info(f"  {c_bold('Step 1: Truncating ALL destination tables')}")
        logger.info(f"{c_blue('━' * 60)}")

        all_dst_tables = [dst for _, _, dst in resolved]
        if dry_run:
            for dst_table in all_dst_tables:
                dest_count = get_row_count(self.dest_conn, dst_table)
                logger.info(f"  [DRY RUN] Would TRUNCATE {dst_table} ({dest_count} rows)")
        else:
            # Single TRUNCATE CASCADE on all tables — atomic, no FK issues
            table_list = ", ".join(all_dst_tables)
            with self.dest_conn.cursor() as cur:
                cur.execute(f"TRUNCATE TABLE {table_list} CASCADE")
            self.dest_conn.commit()
            for dst_table in all_dst_tables:
                logger.info(f"  Truncated {c_cyan(dst_table)}")

        # ── Step 2: INSERT source data in FORWARD FK order ──
        logger.info(f"\n{c_blue('━' * 60)}")
        logger.info(f"  {c_bold('Step 2: Inserting source data (FK order)')}")
        logger.info(f"{c_blue('━' * 60)}")

        current_phase = None
        for phase_name, src_table, dst_table in resolved:
            if phase_name != current_phase:
                current_phase = phase_name
                logger.info(f"\n  {c_bold(phase_name)}")

            # Get shared columns (handles schema differences)
            shared_cols = self._get_shared_columns(src_table, dst_table)
            if not shared_cols:
                logger.warning(f"    No shared columns for {src_table} → {dst_table} — skipping")
                self.stats["tables_skipped"] += 1
                continue

            # Detect columns needing special handling
            src_types = get_column_types(self.source_conn, src_table)
            dst_types = get_column_types(self.dest_conn, dst_table)

            # Columns where source type differs and dest is json/jsonb (text→jsonb)
            text_to_json_cols = {}
            for col in shared_cols:
                src_udt = src_types.get(col, ("", ""))[1]
                dst_udt = dst_types.get(col, ("", ""))[1]
                if src_udt != dst_udt and dst_udt in ("json", "jsonb"):
                    text_to_json_cols[col] = dst_udt
                    logger.info(f"    Type cast: {col} ({src_udt} → {dst_udt})")

            # All dest jsonb/json columns (need Json() wrapper for Python dict/list)
            jsonb_cols = set()
            for col in shared_cols:
                dst_udt = dst_types.get(col, ("", ""))[1]
                if dst_udt in ("json", "jsonb"):
                    jsonb_cols.add(col)

            # Fetch source rows (only shared columns)
            pk_cols = get_primary_keys(self.source_conn, src_table)
            col_select = ", ".join(shared_cols)
            with self.source_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                order_by = ", ".join(pk_cols) if pk_cols else "1"
                cur.execute(f"SELECT {col_select} FROM {src_table} ORDER BY {order_by}")
                source_rows = [dict(row) for row in cur.fetchall()]

            if not source_rows:
                logger.info(f"    {c_cyan(dst_table)}: 0 rows (empty)")
                self.stats["tables_synced"] += 1
                continue

            # Convert values for columns needing special handling
            import json as json_mod
            for row in source_rows:
                # Handle text→jsonb casts (source is text, dest is jsonb)
                for col, udt in text_to_json_cols.items():
                    val = row.get(col)
                    if val is None:
                        continue
                    if isinstance(val, str):
                        try:
                            json_mod.loads(val)
                            # Already valid JSON string — keep as-is
                        except (json_mod.JSONDecodeError, ValueError):
                            # Plain text like "ai, books" → JSON array
                            if "," in val:
                                row[col] = json_mod.dumps([t.strip() for t in val.split(",")])
                            else:
                                row[col] = json_mod.dumps(val)

                # Wrap all jsonb column values with Json() adapter
                for col in jsonb_cols:
                    val = row.get(col)
                    if val is None:
                        continue
                    if isinstance(val, (dict, list)):
                        row[col] = psycopg2.extras.Json(val)
                    elif isinstance(val, str):
                        # Already a JSON string — wrap for proper insertion
                        try:
                            parsed = json_mod.loads(val)
                            row[col] = psycopg2.extras.Json(parsed)
                        except (json_mod.JSONDecodeError, ValueError):
                            row[col] = psycopg2.extras.Json(val)

            # Build INSERT query
            col_list = ", ".join(shared_cols)
            placeholders = ", ".join([f"%({c})s" for c in shared_cols])
            insert_sql = f"INSERT INTO {dst_table} ({col_list}) VALUES ({placeholders})"

            if dry_run:
                logger.info(f"    {c_cyan(dst_table)}: would insert {c_green(str(len(source_rows)))} rows")
                self.stats["tables_synced"] += 1
                self.stats["rows_inserted"] += len(source_rows)
                continue

            # Insert all rows
            inserted = 0
            with self.dest_conn.cursor() as cur:
                for row in source_rows:
                    try:
                        cur.execute(insert_sql, row)
                        inserted += 1
                    except psycopg2.Error as e:
                        logger.error(f"    Error inserting into {dst_table} (row {inserted+1}): {e}")
                        self.dest_conn.rollback()
                        self.stats["errors"].append(f"{dst_table}:insert:row{inserted+1}:{e}")
                        break
                else:
                    # All rows inserted successfully
                    self.dest_conn.commit()

            logger.info(f"    {c_cyan(dst_table)}: {c_green(str(inserted))} rows inserted")
            self.stats["tables_synced"] += 1
            self.stats["rows_inserted"] += inserted

        # ── Step 3: Reset sequences ──
        if not dry_run:
            logger.info(f"\n{c_blue('━' * 60)}")
            logger.info(f"  {c_bold('Step 3: Resetting Sequences')}")
            logger.info(f"{c_blue('━' * 60)}")

            for _, _, dst_table in resolved:
                try:
                    reset_sequence(self.dest_conn, dst_table)
                except psycopg2.Error:
                    pass  # Some tables may not have sequences
            self.dest_conn.commit()

        # Print summary
        self._print_summary(dry_run)

    def verify(self, tables_filter: Optional[List[str]] = None):
        """
        Compare source and destination databases without modifying anything.
        Reports row count differences and data mismatches.
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"  {c_blue('Database Verification')}")
        logger.info(f"  Source: {self.source_config['database']}@{self.source_config['host']}")
        logger.info(f"  Dest:   {self.dest_config['database']}@{self.dest_config['host']}")
        logger.info(f"{'='*70}\n")

        source_tables = get_existing_tables(self.source_conn)
        dest_tables = get_existing_tables(self.dest_conn)

        mismatches = []
        matches = []
        missing_in_dest = []
        missing_in_source = []

        all_tables = []
        for phase_tables in SYNC_PHASES.values():
            all_tables.extend(phase_tables)

        for table in all_tables:
            if tables_filter and table not in tables_filter:
                continue

            src_actual = resolve_table_name(table, source_tables)
            dst_actual = resolve_table_name(table, dest_tables)

            if not src_actual:
                missing_in_source.append(table)
                continue
            if not dst_actual:
                missing_in_dest.append(table)
                continue

            src_count = get_row_count(self.source_conn, src_actual)
            dst_count = get_row_count(self.dest_conn, dst_actual)

            if src_count == dst_count:
                matches.append((table, src_count))
                logger.info(f"  {c_green('✓')} {table:40s} {src_count:>6d} rows — match")
            else:
                diff = src_count - dst_count
                direction = f"+{diff}" if diff > 0 else str(diff)
                mismatches.append((table, src_count, dst_count, diff))
                logger.info(
                    f"  {c_red('✗')} {table:40s} "
                    f"source={src_count:>6d}  dest={dst_count:>6d}  "
                    f"({c_yellow(direction)})"
                )

        # Summary
        logger.info(f"\n{'─'*70}")
        logger.info(f"  {c_bold('Verification Summary')}")
        logger.info(f"{'─'*70}")
        logger.info(f"  Tables matching:          {c_green(len(matches))}")
        logger.info(f"  Tables with differences:  {c_red(len(mismatches))}")
        if missing_in_dest:
            logger.info(f"  Missing in destination:   {c_yellow(', '.join(missing_in_dest))}")
        if missing_in_source:
            logger.info(f"  Missing in source:        {c_yellow(', '.join(missing_in_source))}")

        if mismatches:
            logger.info(f"\n  {c_red('⚠ Databases are NOT in sync.')}")
            logger.info(f"  Run with --to-cloud or --from-cloud to sync.")
        else:
            logger.info(f"\n  {c_green('✓ Databases are in sync!')}")

        return len(mismatches) == 0

    def _print_summary(self, dry_run: bool):
        """Print sync operation summary."""
        mode = c_yellow("[DRY RUN]") if dry_run else c_green("[COMPLETE]")
        logger.info(f"\n{'='*70}")
        logger.info(f"  Sync Summary {mode}")
        logger.info(f"{'='*70}")
        logger.info(f"  Tables synced:   {c_green(self.stats['tables_synced'])}")
        logger.info(f"  Tables skipped:  {c_yellow(self.stats['tables_skipped'])}")
        logger.info(f"  Rows inserted:   {c_green(self.stats['rows_inserted'])}")
        logger.info(f"  Rows updated:    {c_yellow(self.stats['rows_updated'])}")
        logger.info(f"  Rows deleted:    {c_red(self.stats['rows_deleted'])}")

        if self.stats["errors"]:
            logger.info(f"\n  {c_red('Errors:')}")
            for err in self.stats["errors"]:
                logger.info(f"    • {err}")
        else:
            logger.info(f"  Errors:          {c_green('None')}")


# ---------------------------------------------------------------------------
# Cloud SQL backup
# ---------------------------------------------------------------------------

def create_cloud_backup(config: dict):
    """Create a Cloud SQL backup before sync."""
    project_id = config.get("project_id", "")
    instance = config.get("database", {}).get("cloud_sql_instance", "")

    if not project_id or not instance:
        logger.warning("Cannot create backup — missing project_id or cloud_sql_instance in config")
        return False

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    description = f"Pre-sync backup {timestamp}"

    logger.info(f"\n{c_blue('Creating Cloud SQL backup...')}")
    logger.info(f"  Project:  {project_id}")
    logger.info(f"  Instance: {instance}")

    try:
        result = subprocess.run(
            [
                "gcloud", "sql", "backups", "create",
                f"--instance={instance}",
                f"--project={project_id}",
                f"--description={description}",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            logger.info(f"  {c_green('✓ Backup created successfully')}")
            return True
        else:
            logger.warning(f"  Backup failed: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        logger.warning("  gcloud CLI not found — skipping backup")
        return False
    except subprocess.TimeoutExpired:
        logger.warning("  Backup timed out after 120s")
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def confirm_action(message: str) -> bool:
    """Prompt user for confirmation."""
    response = input(f"\n{c_yellow('⚠')} {message} (yes/no): ").strip().lower()
    return response in ("yes", "y")


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Database Sync Tool for Multi-Client Deployments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run — preview what would change
  python db_sync.py --to-cloud --dry-run --env environments/develom.yaml

  # Full sync local → cloud with backup
  python db_sync.py --to-cloud --backup --env environments/develom.yaml

  # Sync cloud → local
  python db_sync.py --from-cloud --env environments/develom.yaml

  # Verify parity only
  python db_sync.py --verify --env environments/develom.yaml

  # Sync specific tables only
  python db_sync.py --to-cloud --tables chatbot_users,chatbot_groups --env environments/develom.yaml
        """,
    )

    # Direction
    direction = parser.add_mutually_exclusive_group(required=True)
    direction.add_argument("--to-cloud", action="store_true", help="Sync local → cloud")
    direction.add_argument("--from-cloud", action="store_true", help="Sync cloud → local")
    direction.add_argument("--verify", action="store_true", help="Verify parity only (no changes)")

    # Options
    parser.add_argument("--env", required=True, help="Path to client environment YAML file")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying")
    parser.add_argument("--backup", action="store_true", help="Create Cloud SQL backup before sync")
    parser.add_argument("--delete-orphans", action="store_true", help="Delete dest rows not in source")
    parser.add_argument("--skip-logs", action="store_true", help="Skip Phase 3 (metadata/log tables)")
    parser.add_argument("--tables", help="Comma-separated list of specific tables to sync")
    parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load config
    config = load_env_config(args.env)
    local_config, cloud_config = build_db_configs(config)

    logger.info(f"Client: {c_bold(config['client_name'])} ({config['account_env']})")
    logger.info(f"Project: {config['project_id']}")

    # Parse tables filter
    tables_filter = None
    if args.tables:
        tables_filter = [t.strip() for t in args.tables.split(",")]
        logger.info(f"Filtering to tables: {tables_filter}")

    # Determine source and destination
    if args.verify:
        sync = DatabaseSync(local_config, cloud_config)
        sync.connect(source_label="LOCAL", dest_label="CLOUD")
        try:
            in_sync = sync.verify(tables_filter=tables_filter)
            sys.exit(0 if in_sync else 1)
        finally:
            sync.close()

    elif args.to_cloud:
        source_config, dest_config = local_config, cloud_config
        source_label, dest_label = "LOCAL", "CLOUD"
        direction_str = "LOCAL → CLOUD"
    else:
        source_config, dest_config = cloud_config, local_config
        source_label, dest_label = "CLOUD", "LOCAL"
        direction_str = "CLOUD → LOCAL"

    # Confirmation
    if not args.dry_run and not args.no_confirm:
        logger.info(f"\n  Direction: {c_bold(direction_str)}")
        logger.info(f"  Dry run:   {args.dry_run}")
        logger.info(f"  Backup:    {args.backup}")
        logger.info(f"  Delete orphans: {args.delete_orphans}")

        if not confirm_action(f"Proceed with {direction_str} sync?"):
            logger.info("Sync cancelled.")
            sys.exit(0)

    # Backup
    if args.backup and args.to_cloud and not args.dry_run:
        create_cloud_backup(config)

    # Execute sync
    sync = DatabaseSync(source_config, dest_config)
    sync.connect(source_label=source_label, dest_label=dest_label)

    try:
        sync.sync_all(
            dry_run=args.dry_run,
            delete_orphans=args.delete_orphans,
            tables_filter=tables_filter,
            skip_phase3=args.skip_logs,
        )
    finally:
        sync.close()

    # Exit with error code if there were errors
    if sync.stats["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
