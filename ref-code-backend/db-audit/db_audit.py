#!/usr/bin/env python3
"""
Database QA Audit Tool
======================
Audits PostgreSQL database schemas across deployment environments and
compares them against the canonical schema_init.py SCHEMA_DDL.

Modes:
  --env / --target   Single-environment audit
  --export           Also save portable schema snapshot JSON
  --compare FILE...  Offline cross-environment diff of snapshots

See backend/db-audit/README.md for full usage.
"""

import argparse
import datetime
import getpass
import json
import os
import re
import sys
from pathlib import Path

# ── Colour helpers ────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
WHITE  = "\033[37m"

_quiet = False


def _c(colour, text):
    if _quiet:
        return text
    return f"{colour}{text}{RESET}"


def ok(msg):    print(_c(GREEN,  f"  ✅  {msg}"))
def warn(msg):  print(_c(YELLOW, f"  ⚠️   {msg}"))
def fail(msg):  print(_c(RED,    f"  ❌  {msg}"))
def info(msg):  print(_c(CYAN,   f"  ℹ️   {msg}"))
def header(msg):
    if not _quiet:
        print(_c(BOLD, f"\n{'─' * 64}"))
        print(_c(BOLD, f"  {msg}"))
        print(_c(BOLD, f"{'─' * 64}"))
    else:
        print(f"\n=== {msg} ===")


# ── Connection ────────────────────────────────────────────────────────────────

def _resolve_password(config: dict) -> str:
    """Resolve DB password: env var → Secret Manager → interactive prompt."""
    # 1. Environment variable
    pw = os.getenv("DB_PASSWORD", "").strip()
    if pw:
        return pw

    # 2. Secret Manager via ADC
    db_cfg = config.get("database", {})
    secret_name = db_cfg.get("password_secret_name", "").strip()
    project_id = config.get("project_id", "").strip()
    if secret_name and project_id:
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            pw = response.payload.data.decode("UTF-8").strip()
            if pw:
                info(f"Password fetched from Secret Manager ({secret_name})")
                return pw
        except Exception as e:
            warn(f"Secret Manager unavailable ({e}). Falling back to prompt.")

    # 3. Interactive prompt
    db_user = db_cfg.get("user", "adk_app_user")
    db_host = "cloud" if secret_name else "database"
    return getpass.getpass(f"  Enter password for {db_user}@{db_host}: ")


def get_connection(config: dict, target: str):
    """Create a psycopg2 connection based on target."""
    import psycopg2

    db_cfg = config.get("database", {})

    if target == "local":
        local = db_cfg.get("local", {})
        return psycopg2.connect(
            host=local.get("host", "localhost"),
            port=local.get("port", 5433),
            dbname=local.get("name", "adk_agents_db_dev"),
            user=local.get("user", "adk_dev_user"),
            password=local.get("password", "dev_password_123"),
        )

    password = _resolve_password(config)

    if target == "cloud-socket":
        cloud_sql_conn = os.getenv(
            "CLOUD_SQL_CONNECTION_NAME",
            db_cfg.get("cloud_sql_connection", ""),
        )
        socket_dir = f"/cloudsql/{cloud_sql_conn}"
        return psycopg2.connect(
            host=socket_dir,
            dbname=db_cfg.get("name", "adk_agents_db"),
            user=db_cfg.get("user", "adk_app_user"),
            password=password,
        )

    # cloud — via proxy on port 5434
    return psycopg2.connect(
        host="127.0.0.1",
        port=5434,
        dbname=db_cfg.get("name", "adk_agents_db"),
        user=db_cfg.get("user", "adk_app_user"),
        password=password,
    )


# ── Canonical schema parser ───────────────────────────────────────────────────

def _parse_create_table(ddl: str) -> tuple[str, dict]:
    """
    Parse a CREATE TABLE IF NOT EXISTS statement.
    Returns (table_name, {col_name: {type, nullable, default}}).
    """
    # Extract table name
    m = re.search(
        r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)\s*\((.+)\)",
        ddl, re.IGNORECASE | re.DOTALL
    )
    if not m:
        return None, {}

    table_name = m.group(1).lower()
    body = m.group(2)

    columns = {}
    # Split on commas not inside parentheses
    depth = 0
    current = []
    parts = []
    for ch in body:
        if ch == '(':
            depth += 1
            current.append(ch)
        elif ch == ')':
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append(''.join(current).strip())

    for part in parts:
        part = part.strip()
        if not part:
            continue
        upper = part.upper()
        # Skip constraints
        if any(upper.startswith(kw) for kw in (
            "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK", "CONSTRAINT", "EXCLUDE"
        )):
            continue

        # Parse: col_name TYPE [NOT NULL] [DEFAULT expr]
        col_m = re.match(r"(\w+)\s+([A-Z][A-Z0-9_\(\), ]*?)(\s+.*)?$", part, re.IGNORECASE)
        if not col_m:
            continue

        col_name = col_m.group(1).lower()
        col_type = col_m.group(2).strip().lower()
        rest = (col_m.group(3) or "").upper()

        nullable = "NOT NULL" not in rest
        default = None
        default_m = re.search(r"DEFAULT\s+(\S+(?:\s*::\s*\w+(?:\[\])?)?)", part, re.IGNORECASE)
        if default_m:
            default = default_m.group(1).lower()

        columns[col_name] = {
            "type": col_type,
            "nullable": nullable,
            "default": default,
        }

    return table_name, columns


def _parse_create_index(ddl: str) -> tuple[str, str]:
    """Returns (index_name, table_name) from a CREATE INDEX statement."""
    m = re.search(
        r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS\s+(\w+)\s+ON\s+(\w+)",
        ddl, re.IGNORECASE
    )
    if m:
        return m.group(1).lower(), m.group(2).lower()
    return None, None


def build_canonical_schema() -> dict:
    """
    Import SCHEMA_DDL from schema_init.py and parse into a normalized dict:
    {table_name: {columns: {...}, indexes: [...]}}
    """
    # Inject path so we can import schema_init without installing the app
    script_dir = Path(__file__).resolve().parent
    src_path = script_dir.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    try:
        from database.schema_init import SCHEMA_DDL
    except ImportError as e:
        print(_c(RED, f"  ❌  Cannot import SCHEMA_DDL from schema_init.py: {e}"))
        print(_c(RED, f"      Make sure you run this from the repo root."))
        sys.exit(2)

    schema = {}  # table_name → {columns, indexes}

    for ddl in SCHEMA_DDL:
        ddl_stripped = ddl.strip()
        upper = ddl_stripped.upper()

        if upper.startswith("CREATE TABLE"):
            table_name, columns = _parse_create_table(ddl_stripped)
            if table_name:
                if table_name not in schema:
                    schema[table_name] = {"columns": {}, "indexes": []}
                schema[table_name]["columns"] = columns

        elif upper.startswith("CREATE") and "INDEX" in upper:
            idx_name, tbl_name = _parse_create_index(ddl_stripped)
            if idx_name and tbl_name:
                if tbl_name not in schema:
                    schema[tbl_name] = {"columns": {}, "indexes": []}
                schema[tbl_name]["indexes"].append(idx_name)

        # ALTER TABLE statements (ADD COLUMN, RENAME) are intentionally skipped
        # for the canonical schema — they represent migration guards, not the
        # ideal end state. We compare against CREATE TABLE definitions only.

    return schema


# ── Live schema introspection ─────────────────────────────────────────────────

def introspect_live_schema(conn) -> dict:
    """
    Query information_schema + pg_indexes to build the same normalized dict
    shape as build_canonical_schema().
    """
    cur = conn.cursor()
    schema = {}

    # Tables
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cur.fetchall()]

    for table in tables:
        # Columns
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
        """, (table,))
        columns = {}
        for col_name, data_type, is_nullable, col_default in cur.fetchall():
            columns[col_name.lower()] = {
                "type": data_type.lower(),
                "nullable": (is_nullable == "YES"),
                "default": col_default.lower() if col_default else None,
            }

        # Indexes
        cur.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = %s
        """, (table,))
        indexes = [row[0].lower() for row in cur.fetchall()]

        schema[table.lower()] = {"columns": columns, "indexes": indexes}

    cur.close()
    return schema


def get_db_version(conn) -> str:
    cur = conn.cursor()
    cur.execute("SELECT version()")
    row = cur.fetchone()
    cur.close()
    if row:
        # "PostgreSQL 14.11 on x86_64-..." → "PostgreSQL 14.11"
        return " ".join(row[0].split()[:2])
    return "unknown"


def get_row_counts(conn, tables: list) -> dict:
    """Return {table_name: row_count} for the given tables."""
    counts = {}
    cur = conn.cursor()
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
            counts[table] = cur.fetchone()[0]
        except Exception:
            conn.rollback()
            counts[table] = None
    cur.close()
    return counts


# ── Schema diff engine ────────────────────────────────────────────────────────

STALE_COLUMNS = {
    "users": {"username", "hashed_password", "auth_provider"},
}

SEVERITY_FAIL = "FAIL"
SEVERITY_WARN = "WARN"
SEVERITY_PASS = "PASS"


def diff_schema(canonical: dict, live: dict) -> list[dict]:
    """
    Compare canonical vs live schema. Returns list of finding dicts:
    {severity, category, table, column, message}
    """
    findings = []

    def finding(severity, category, table, column, message):
        findings.append({
            "severity": severity,
            "category": category,
            "table": table,
            "column": column,
            "message": message,
        })

    canonical_tables = set(canonical.keys())
    live_tables = set(live.keys())

    # Missing tables
    for t in sorted(canonical_tables - live_tables):
        finding(SEVERITY_FAIL, "MISSING_TABLE", t, None,
                f"Table '{t}' defined in schema_init.py but not found in DB")

    # Extra tables (warn only)
    for t in sorted(live_tables - canonical_tables):
        finding(SEVERITY_WARN, "EXTRA_TABLE", t, None,
                f"Table '{t}' exists in DB but not in canonical schema")

    # Stale columns that should have been dropped
    for table, stale_cols in STALE_COLUMNS.items():
        if table in live:
            for col in stale_cols:
                if col in live[table]["columns"]:
                    finding(SEVERITY_FAIL, "STALE_COLUMN", table, col,
                            f"Column '{table}.{col}' was dropped by migration 014 "
                            f"but still exists in DB")

    # Per-table column and index checks
    for table in sorted(canonical_tables & live_tables):
        canon_cols = canonical[table]["columns"]
        live_cols  = live[table]["columns"]
        canon_idx  = set(canonical[table]["indexes"])
        live_idx   = set(live[table]["indexes"])

        # Missing columns
        for col in sorted(set(canon_cols) - set(live_cols)):
            finding(SEVERITY_FAIL, "MISSING_COLUMN", table, col,
                    f"Column '{table}.{col}' expected but missing from DB")

        # Extra columns (warn)
        for col in sorted(set(live_cols) - set(canon_cols)):
            # Skip known stale columns (already reported above)
            stale = STALE_COLUMNS.get(table, set())
            if col not in stale:
                finding(SEVERITY_WARN, "EXTRA_COLUMN", table, col,
                        f"Column '{table}.{col}' exists in DB but not in canonical schema")

        # Type mismatches
        for col in sorted(set(canon_cols) & set(live_cols)):
            canon_type = canon_cols[col]["type"]
            live_type  = live_cols[col]["type"]
            # Normalize common aliases: integer ↔ int4, varchar ↔ character varying
            if not _types_match(canon_type, live_type):
                finding(SEVERITY_WARN, "TYPE_MISMATCH", table, col,
                        f"Column '{table}.{col}': canonical type '{canon_type}' "
                        f"vs live type '{live_type}'")

        # Missing indexes
        for idx in sorted(canon_idx - live_idx):
            finding(SEVERITY_WARN, "MISSING_INDEX", table, None,
                    f"Index '{idx}' on '{table}' defined in schema_init.py but absent from DB")

    return findings


def _types_match(canonical_type: str, live_type: str) -> bool:
    """Loose type equivalence — PostgreSQL reports types differently from DDL."""
    equivalences = [
        {"integer", "int4", "int"},
        {"bigint", "int8"},
        {"smallint", "int2"},
        {"boolean", "bool"},
        {"character varying", "varchar"},
        {"text", "text"},
        {"timestamp without time zone", "timestamp"},
        {"jsonb", "jsonb"},
        {"serial", "integer", "int4"},
    ]
    ct = canonical_type.lower().split("(")[0].strip()
    lt = live_type.lower().split("(")[0].strip()
    if ct == lt:
        return True
    for group in equivalences:
        if ct in group and lt in group:
            return True
    return False


# ── Data integrity checks ─────────────────────────────────────────────────────

def run_data_integrity_checks(conn, live_schema: dict) -> list[dict]:
    """
    Run targeted data quality queries. Returns list of finding dicts.
    Only runs checks for tables/columns that actually exist in the live DB.
    """
    findings = []
    cur = conn.cursor()

    def finding(severity, check, message, count=None):
        findings.append({
            "severity": severity,
            "check": check,
            "message": message,
            "count": count,
        })

    def table_exists(t): return t in live_schema
    def col_exists(t, c): return table_exists(t) and c in live_schema[t]["columns"]

    # ── Empty critical tables ─────────────────────────────────────────────────
    critical_tables = ["agents", "chatbot_groups", "corpora"]
    for t in critical_tables:
        if table_exists(t):
            cur.execute(f"SELECT COUNT(*) FROM {t}")  # noqa: S608
            count = cur.fetchone()[0]
            if count == 0:
                finding(SEVERITY_WARN, "EMPTY_TABLE",
                        f"Table '{t}' has 0 rows — seed data may not have run", count=0)
            else:
                finding(SEVERITY_PASS, "EMPTY_TABLE",
                        f"Table '{t}' has {count} rows", count=count)

    # ── NULL in required fields ───────────────────────────────────────────────
    required_not_null = [
        ("users",          "email"),
        ("agents",         "config_path"),
        ("agents",         "name"),
        ("corpora",        "name"),
        ("chatbot_users",  "email"),
        ("chatbot_groups", "name"),
    ]
    for table, col in required_not_null:
        if col_exists(table, col):
            cur.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL"  # noqa: S608
            )
            count = cur.fetchone()[0]
            if count > 0:
                finding(SEVERITY_FAIL, "NULL_REQUIRED",
                        f"'{table}.{col}' has {count} NULL value(s) — required field",
                        count=count)

    # ── Duplicate unique values ───────────────────────────────────────────────
    unique_checks = [
        ("users",         "email"),
        ("chatbot_users", "email"),
        ("chatbot_users", "username"),
        ("agents",        "name"),
        ("corpora",       "name"),
        ("groups",        "name"),
    ]
    for table, col in unique_checks:
        if col_exists(table, col):
            cur.execute(f"""
                SELECT COUNT(*) FROM (
                    SELECT {col} FROM {table}
                    GROUP BY {col} HAVING COUNT(*) > 1
                ) AS dups
            """)  # noqa: S608
            count = cur.fetchone()[0]
            if count > 0:
                finding(SEVERITY_FAIL, "DUPLICATE_UNIQUE",
                        f"'{table}.{col}' has {count} duplicate value(s) — must be unique",
                        count=count)

    # ── FK orphans ────────────────────────────────────────────────────────────
    fk_checks = [
        ("user_sessions",   "user_id",   "users",   "id"),
        ("user_agent_access","user_id",  "users",   "id"),
        ("user_agent_access","agent_id", "agents",  "id"),
        ("chatbot_user_groups","chatbot_user_id","chatbot_users","id"),
        ("chatbot_user_groups","chatbot_group_id","chatbot_groups","id"),
        ("group_corpus_access","group_id","groups", "id"),
        ("group_corpus_access","corpus_id","corpora","id"),
    ]
    for child_table, child_col, parent_table, parent_col in fk_checks:
        if col_exists(child_table, child_col) and table_exists(parent_table):
            cur.execute(f"""
                SELECT COUNT(*) FROM {child_table} c
                WHERE c.{child_col} IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM {parent_table} p WHERE p.{parent_col} = c.{child_col}
                  )
            """)  # noqa: S608
            count = cur.fetchone()[0]
            if count > 0:
                finding(SEVERITY_FAIL, "FK_ORPHAN",
                        f"{count} orphan row(s) in '{child_table}.{child_col}' "
                        f"with no matching '{parent_table}.{parent_col}'",
                        count=count)

    # ── Stale data in dropped columns ─────────────────────────────────────────
    for table, stale_cols in STALE_COLUMNS.items():
        if table_exists(table):
            for col in stale_cols:
                if col_exists(table, col):
                    cur.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL"  # noqa: S608
                    )
                    count = cur.fetchone()[0]
                    if count > 0:
                        finding(SEVERITY_WARN, "STALE_DATA",
                                f"'{table}.{col}' was dropped but still has {count} "
                                f"non-NULL value(s)",
                                count=count)

    cur.close()
    return findings


# ── Environment identity ──────────────────────────────────────────────────────

def build_env_identity(config: dict, db_version: str, target: str) -> dict:
    db_cfg = config.get("database", {})
    return {
        "environment":   config.get("account_env", config.get("client_name", "unknown")),
        "client_name":   config.get("client_name", "unknown"),
        "project":       config.get("project_id", "unknown"),
        "region":        config.get("region", "unknown"),
        "db_name":       db_cfg.get("name", "adk_agents_db"),
        "db_user":       db_cfg.get("user", "adk_app_user"),
        "cloud_sql":     db_cfg.get("cloud_sql_connection", "unknown"),
        "db_version":    db_version,
        "target":        target,
        "audit_time":    datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def print_env_identity(identity: dict):
    header(f"Environment: {identity['environment'].upper()}")
    pad = 16
    for label, key in [
        ("Client",       "client_name"),
        ("Project",      "project"),
        ("Region",       "region"),
        ("DB Name",      "db_name"),
        ("DB User",      "db_user"),
        ("Cloud SQL",    "cloud_sql"),
        ("DB Version",   "db_version"),
        ("Target",       "target"),
        ("Audit Time",   "audit_time"),
    ]:
        print(f"  {label:<{pad}}: {identity[key]}")


# ── Report output ─────────────────────────────────────────────────────────────

def print_schema_findings(findings: list[dict]) -> tuple[int, int, int]:
    """Print schema diff findings. Returns (pass, warn, fail) counts."""
    passes = warns = fails = 0

    # Group by table
    by_table = {}
    for f in findings:
        t = f.get("table", "_")
        by_table.setdefault(t, []).append(f)

    header("Schema Audit")
    if not findings:
        ok("All tables and columns match canonical schema_init.py")
        return 0, 0, 0

    for table in sorted(by_table.keys()):
        for f in by_table[table]:
            if f["severity"] == SEVERITY_FAIL:
                fails += 1
                fail(f["message"])
            elif f["severity"] == SEVERITY_WARN:
                warns += 1
                warn(f["message"])
            else:
                passes += 1
                ok(f["message"])

    return passes, warns, fails


def print_integrity_findings(findings: list[dict]) -> tuple[int, int, int]:
    """Print data integrity findings. Returns (pass, warn, fail) counts."""
    passes = warns = fails = 0

    header("Data Integrity")
    if not findings:
        ok("No data integrity issues found")
        return 0, 0, 0

    for f in findings:
        if f["severity"] == SEVERITY_FAIL:
            fails += 1
            fail(f["message"])
        elif f["severity"] == SEVERITY_WARN:
            warns += 1
            warn(f["message"])
        else:
            passes += 1
            ok(f["message"])

    return passes, warns, fails


def print_summary(s_pass, s_warn, s_fail, i_pass, i_warn, i_fail):
    total_pass = s_pass + i_pass
    total_warn = s_warn + i_warn
    total_fail = s_fail + i_fail
    header("Summary")
    print(f"  {'Schema':20s}  ✅ {s_pass} pass   ⚠️  {s_warn} warn   ❌ {s_fail} fail")
    print(f"  {'Data Integrity':20s}  ✅ {i_pass} pass   ⚠️  {i_warn} warn   ❌ {i_fail} fail")
    print(f"  {'─' * 52}")
    print(f"  {'TOTAL':20s}  ✅ {total_pass} pass   ⚠️  {total_warn} warn   ❌ {total_fail} fail")
    if total_fail > 0:
        print(_c(RED, f"\n  ❌  AUDIT FAILED — {total_fail} critical issue(s) found"))
    elif total_warn > 0:
        print(_c(YELLOW, f"\n  ⚠️   AUDIT PASSED WITH WARNINGS — {total_warn} warning(s)"))
    else:
        print(_c(GREEN, f"\n  ✅  AUDIT PASSED — no issues found"))
    return total_fail, total_warn


def save_report(identity: dict, schema_findings: list, integrity_findings: list,
                s_counts: tuple, i_counts: tuple):
    """Save full audit report JSON."""
    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)

    env = identity["environment"]
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"{env}_{ts}.json"

    report = {
        "environment": env,
        "identity": identity,
        "summary": {
            "schema":    {"pass": s_counts[0], "warn": s_counts[1], "fail": s_counts[2]},
            "integrity": {"pass": i_counts[0], "warn": i_counts[1], "fail": i_counts[2]},
            "total": {
                "pass": s_counts[0] + i_counts[0],
                "warn": s_counts[1] + i_counts[1],
                "fail": s_counts[2] + i_counts[2],
            },
        },
        "schema_findings":    schema_findings,
        "integrity_findings": integrity_findings,
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    info(f"Report saved: {report_path}")
    return report_path


def save_snapshot(identity: dict, live_schema: dict, row_counts: dict):
    """Save portable schema snapshot JSON for use with --compare."""
    snap_dir = Path(__file__).parent / "snapshots"
    snap_dir.mkdir(exist_ok=True)

    env = identity["environment"]
    snap_path = snap_dir / f"{env}.json"

    snapshot = {
        "environment": env,
        "project":     identity["project"],
        "region":      identity["region"],
        "cloud_sql":   identity["cloud_sql"],
        "db_version":  identity["db_version"],
        "audit_time":  identity["audit_time"],
        "schema":      live_schema,
        "row_counts":  row_counts,
    }

    with open(snap_path, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    info(f"Snapshot saved: {snap_path}")
    return snap_path


# ── Cross-environment comparison ──────────────────────────────────────────────

def run_compare(snapshot_paths: list[str]):
    """
    Load snapshot JSONs and produce a cross-environment schema comparison.
    No live DB connection required.
    """
    snapshots = []
    for path in snapshot_paths:
        p = Path(path)
        if not p.exists():
            print(_c(RED, f"  ❌  Snapshot not found: {path}"))
            sys.exit(2)
        with open(p) as f:
            snapshots.append(json.load(f))

    env_names = [s["environment"] for s in snapshots]
    canonical  = build_canonical_schema()

    header(f"Cross-Environment Comparison: {' | '.join(env_names)}")
    for s in snapshots:
        print(f"  {s['environment']:<12}: {s['db_version']}  "
              f"(snapshot: {s['audit_time'][:19]})")

    # Collect all table/column keys across canonical + all envs
    all_tables = set(canonical.keys())
    for s in snapshots:
        all_tables.update(s["schema"].keys())

    divergences = []
    identical_tables = []
    total_cells = 0
    pass_cells = 0

    header("Schema Divergences")

    col_w = 36
    env_w = 12

    # Header row
    hdr = f"  {'TABLE.COLUMN':<{col_w}}"
    hdr += f"  {'CANONICAL':<{env_w}}"
    for env in env_names:
        hdr += f"  {env.upper():<{env_w}}"
    print(_c(BOLD, hdr))
    print("  " + "─" * (col_w + (env_w + 2) * (len(env_names) + 1)))

    found_divergence = False

    for table in sorted(all_tables):
        canon_cols = canonical.get(table, {}).get("columns", {})
        live_cols_per_env = [s["schema"].get(table, {}).get("columns", {}) for s in snapshots]

        # Check if table is entirely missing from any env
        table_missing_canonical = table not in canonical
        table_missing_envs = [table not in s["schema"] for s in snapshots]

        # Get all columns for this table
        all_cols = set(canon_cols.keys())
        for lc in live_cols_per_env:
            all_cols.update(lc.keys())

        table_has_divergence = False

        # Table-level missing check
        if any(table_missing_envs) or table_missing_canonical:
            canon_status = "absent" if table_missing_canonical else "✅ present"
            env_statuses = []
            for i, missing in enumerate(table_missing_envs):
                env_statuses.append("❌ missing" if missing else "✅ present")

            row = f"  {(table + ' (TABLE)'):<{col_w}}  {canon_status:<{env_w}}"
            for st in env_statuses:
                row += f"  {st:<{env_w}}"

            all_statuses = [canon_status] + env_statuses
            if len(set(all_statuses)) > 1:
                print(_c(YELLOW if "absent" not in canon_status else RED, row))
                divergences.append({
                    "table": table, "column": None,
                    "canonical": canon_status,
                    **{env: st for env, st in zip(env_names, env_statuses)},
                })
                found_divergence = True
                table_has_divergence = True
            continue

        # Column-level checks for tables present everywhere
        for col in sorted(all_cols):
            total_cells += 1
            in_canon = col in canon_cols
            in_envs  = [col in lc for lc in live_cols_per_env]

            # Check stale
            is_stale = col in STALE_COLUMNS.get(table, set())

            canon_status = "absent" if not in_canon else "✅ ok"
            if is_stale and in_canon:
                canon_status = "⚠️ stale"

            env_statuses = []
            for i, present in enumerate(in_envs):
                if not present:
                    env_statuses.append("❌ missing")
                elif is_stale:
                    env_statuses.append("⚠️ present")
                else:
                    env_statuses.append("✅ ok")

            all_statuses = [canon_status] + env_statuses
            all_ok = all(
                s in ("✅ ok", "absent") or (not in_canon and not any(in_envs))
                for s in all_statuses
            )

            # Only print rows with divergence or issues
            if len(set(all_statuses)) > 1 or "❌" in str(all_statuses) or "⚠️" in str(all_statuses):
                label = f"{table}.{col}"
                row = f"  {label:<{col_w}}  {canon_status:<{env_w}}"
                for st in env_statuses:
                    row += f"  {st:<{env_w}}"

                severity_colour = RED if "❌" in row else YELLOW
                print(_c(severity_colour, row))

                divergences.append({
                    "table": table, "column": col,
                    "canonical": canon_status,
                    **{env: st for env, st in zip(env_names, env_statuses)},
                })
                found_divergence = True
                table_has_divergence = True
            else:
                pass_cells += 1

        if not table_has_divergence:
            identical_tables.append(table)

    if not found_divergence:
        ok("All schemas are identical across all environments and match canonical")

    # Row count divergences
    header("Seed Data (Row Counts)")
    critical = ["agents", "chatbot_groups", "corpora", "chatbot_users"]
    count_hdr = f"  {'TABLE':<{col_w}}"
    for env in env_names:
        count_hdr += f"  {env.upper():<{env_w}}"
    print(_c(BOLD, count_hdr))
    print("  " + "─" * (col_w + (env_w + 2) * len(env_names)))

    for table in sorted(critical):
        row_data = [s.get("row_counts", {}).get(table) for s in snapshots]
        row_str = f"  {table:<{col_w}}"
        for count in row_data:
            cell = "n/a" if count is None else str(count)
            colour = YELLOW if count == 0 else ""
            row_str += f"  {_c(colour, cell):<{env_w}}"
        print(row_str)

    # Summary
    header("Comparison Summary")
    print(f"  Environments compared : {', '.join(env_names)}")
    print(f"  Divergent items       : {len(divergences)}")
    print(f"  Identical tables      : {len(identical_tables)}")
    if identical_tables:
        info(f"  Matching: {', '.join(sorted(identical_tables))}")

    # Save compare report
    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"compare_{ts}.json"
    report = {
        "audit_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "environments": env_names,
        "summary": {
            "divergences": len(divergences),
            "identical_tables": len(identical_tables),
        },
        "divergences": divergences,
        "identical_tables": sorted(identical_tables),
        "row_counts": {
            s["environment"]: s.get("row_counts", {}) for s in snapshots
        },
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    info(f"Compare report saved: {report_path}")

    return 1 if divergences else 0


# ── Single-environment audit entrypoint ───────────────────────────────────────

def run_audit(env_path: str, target: str, do_export: bool) -> int:
    """Run a single-environment audit. Returns exit code."""
    import yaml

    env_path = Path(env_path)
    if not env_path.exists():
        print(_c(RED, f"  ❌  Environment file not found: {env_path}"))
        return 2

    with open(env_path) as f:
        config = yaml.safe_load(f)

    # Connect
    header(f"Connecting ({target})")
    try:
        conn = get_connection(config, target)
        conn.autocommit = True
        ok(f"Connected to {config.get('database', {}).get('name', 'adk_agents_db')}")
    except Exception as e:
        print(_c(RED, f"  ❌  Connection failed: {e}"))
        print(_c(YELLOW,
              "      Check Cloud SQL Auth Proxy is running on port 5434 "
              "(for --target cloud).\n"
              "      Run: gcloud auth application-default login\n"
              "           gcloud auth application-default set-quota-project <project-id>"))
        return 2

    db_version = get_db_version(conn)
    identity   = build_env_identity(config, db_version, target)
    print_env_identity(identity)

    # Build schemas
    canonical  = build_canonical_schema()
    live       = introspect_live_schema(conn)

    # Row counts for critical tables
    critical_tables = ["agents", "chatbot_groups", "corpora", "chatbot_users",
                       "users", "chatbot_roles", "chatbot_permissions"]
    row_counts = get_row_counts(conn, [t for t in critical_tables if t in live])

    # Schema diff
    schema_findings = diff_schema(canonical, live)
    s_counts = print_schema_findings(schema_findings)

    # Data integrity
    integrity_findings = run_data_integrity_checks(conn, live)
    i_counts = print_integrity_findings(integrity_findings)

    # Summary
    total_fail, total_warn = print_summary(*s_counts, *i_counts)

    # Persist
    save_report(identity, schema_findings, integrity_findings, s_counts, i_counts)

    if do_export:
        save_snapshot(identity, live, row_counts)

    conn.close()
    return 1 if total_fail > 0 else 0


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    global _quiet

    parser = argparse.ArgumentParser(
        description="Database QA Audit Tool — audit and compare PostgreSQL schemas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single-env audit (Develom/TT/USFS all use --target cloud)
  python db_audit.py --env ../../environments/develom.yaml --target cloud
  python db_audit.py --env ../../environments/tt.yaml      --target cloud

  # Audit + export snapshot for cross-env compare
  python db_audit.py --env ../../environments/develom.yaml --target cloud --export
  python db_audit.py --env ../../environments/usfs.yaml    --target cloud --export

  # Cross-env compare (offline, uses snapshots)
  python db_audit.py --compare snapshots/develom.json snapshots/tt.json snapshots/usfs.json
""",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--env", metavar="YAML",
                       help="Path to environment YAML file (single-env audit)")
    group.add_argument("--compare", nargs="+", metavar="SNAPSHOT",
                       help="Offline cross-env diff of 2+ snapshot JSON files")

    parser.add_argument("--target",
                        choices=["cloud", "cloud-socket", "local"],
                        default="cloud",
                        help="DB target: cloud (proxy:5434), cloud-socket, local (port:5433)")
    parser.add_argument("--export", action="store_true",
                        help="Also save portable schema snapshot to snapshots/<env>.json")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress color output; JSON reports still saved")

    args = parser.parse_args()
    _quiet = args.quiet

    if args.compare:
        sys.exit(run_compare(args.compare))
    else:
        sys.exit(run_audit(args.env, args.target, args.export))


if __name__ == "__main__":
    main()
