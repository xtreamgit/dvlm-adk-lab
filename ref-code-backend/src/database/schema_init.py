"""
Database schema initialization for PostgreSQL.

Uses self-contained, idempotent CREATE TABLE IF NOT EXISTS statements instead
of running migration SQL files. Each DDL statement is executed and committed
individually so one failure doesn't cascade to the rest.

This approach is bulletproof on both fresh databases (new environments like
TT, USFS) and existing ones (develom) — migration files are not reliable for
bootstrapping from scratch because they contain destructive operations
(DROP TABLE), INSERT data, and cross-references that fail on empty databases.
"""

import logging

logger = logging.getLogger(__name__)

# ─── Complete schema DDL ─────────────────────────────────────────────────────
# Ordered so parent tables come before children (FK dependencies respected).
# Every statement is idempotent and safe to re-run.

SCHEMA_DDL = [
    # ── 001: users ───────────────────────────────────────────────────────────
    # NOTE: username, auth_provider, hashed_password removed per migration 014
    # IAP handles all authentication; email is the sole user identifier
    """CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        full_name VARCHAR(255),
        is_active BOOLEAN DEFAULT TRUE,
        default_agent_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        google_id VARCHAR(255)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
    "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",

    # ── 002: user_profiles ───────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS user_profiles (
        id SERIAL PRIMARY KEY,
        user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        theme VARCHAR(50) DEFAULT 'light',
        language VARCHAR(10) DEFAULT 'en',
        timezone VARCHAR(50) DEFAULT 'UTC',
        preferences JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",

    # ── 002: groups ──────────────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS groups (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )""",

    # ── 002: roles ───────────────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS roles (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        description TEXT,
        permissions JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",

    # ── 002: user_groups ─────────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS user_groups (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, group_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_user_groups_user ON user_groups(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_user_groups_group ON user_groups(group_id)",

    # ── 002: group_roles ─────────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS group_roles (
        id SERIAL PRIMARY KEY,
        group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
        role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(group_id, role_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_group_roles_group ON group_roles(group_id)",
    "CREATE INDEX IF NOT EXISTS idx_group_roles_role ON group_roles(role_id)",

    # ── 003: agents ──────────────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS agents (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        display_name VARCHAR(255) NOT NULL,
        description TEXT,
        config_path VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name)",
    "CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active)",

    # ── 003: user_agent_access ───────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS user_agent_access (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, agent_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_user_agent_access_user ON user_agent_access(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_user_agent_access_agent ON user_agent_access(agent_id)",

    # ── 003: corpora ─────────────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS corpora (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        display_name VARCHAR(255),
        description TEXT,
        vertex_corpus_id VARCHAR(255),
        is_active BOOLEAN DEFAULT TRUE,
        gcs_bucket VARCHAR(500),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER REFERENCES users(id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_corpora_name ON corpora(name)",
    "CREATE INDEX IF NOT EXISTS idx_corpora_active ON corpora(is_active)",

    # ── 003: group_corpus_access ─────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS group_corpus_access (
        id SERIAL PRIMARY KEY,
        group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
        corpus_id INTEGER NOT NULL REFERENCES corpora(id) ON DELETE CASCADE,
        permission VARCHAR(50) DEFAULT 'read',
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(group_id, corpus_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_group_corpus_access_group ON group_corpus_access(group_id)",
    "CREATE INDEX IF NOT EXISTS idx_group_corpus_access_corpus ON group_corpus_access(corpus_id)",

    # ── 003: user_sessions ───────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS user_sessions (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(255) UNIQUE NOT NULL,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        active_agent_id INTEGER REFERENCES agents(id),
        active_corpora JSONB DEFAULT '[]'::jsonb,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        message_count INTEGER DEFAULT 0,
        user_query_count INTEGER DEFAULT 0
    )""",
    "CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON user_sessions(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active)",

    # ── 003: session_corpus_selections ────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS session_corpus_selections (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        corpus_id INTEGER NOT NULL REFERENCES corpora(id) ON DELETE CASCADE,
        last_selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, corpus_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_session_corpus_user ON session_corpus_selections(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_session_corpus_corpus ON session_corpus_selections(corpus_id)",

    # ── 004: corpus_audit_log ────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS corpus_audit_log (
        id SERIAL PRIMARY KEY,
        corpus_id INTEGER REFERENCES corpora(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        action VARCHAR(100) NOT NULL,
        changes JSONB,
        metadata JSONB,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS idx_audit_corpus ON corpus_audit_log(corpus_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_user ON corpus_audit_log(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON corpus_audit_log(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_audit_action ON corpus_audit_log(action)",

    # ── 004: corpus_metadata ─────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS corpus_metadata (
        id SERIAL PRIMARY KEY,
        corpus_id INTEGER UNIQUE NOT NULL REFERENCES corpora(id) ON DELETE CASCADE,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_synced_at TIMESTAMP,
        last_synced_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        document_count INTEGER DEFAULT 0,
        last_document_count_update TIMESTAMP,
        sync_status VARCHAR(50) DEFAULT 'active',
        sync_error_message TEXT,
        tags JSONB DEFAULT '[]'::jsonb,
        notes TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_corpus_metadata_corpus ON corpus_metadata(corpus_id)",
    "CREATE INDEX IF NOT EXISTS idx_corpus_metadata_status ON corpus_metadata(sync_status)",

    # ── 004: corpus_sync_schedule ────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS corpus_sync_schedule (
        id SERIAL PRIMARY KEY,
        corpus_id INTEGER REFERENCES corpora(id) ON DELETE CASCADE,
        frequency VARCHAR(50),
        last_run TIMESTAMP,
        next_run TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )""",
    "CREATE INDEX IF NOT EXISTS idx_sync_schedule_corpus ON corpus_sync_schedule(corpus_id)",
    "CREATE INDEX IF NOT EXISTS idx_sync_schedule_active ON corpus_sync_schedule(is_active)",

    # ── 007: chatbot_users ───────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        hashed_password VARCHAR(255),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        created_by INTEGER REFERENCES users(id),
        notes TEXT,
        user_id INTEGER
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_users_username ON chatbot_users(username)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_users_email ON chatbot_users(email)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_users_is_active ON chatbot_users(is_active)",

    # ── 007: chatbot_groups ──────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_groups (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER REFERENCES users(id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_groups_name ON chatbot_groups(name)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_groups_is_active ON chatbot_groups(is_active)",

    # ── 007: chatbot_roles ───────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_roles (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER REFERENCES users(id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_roles_name ON chatbot_roles(name)",

    # ── 007: chatbot_permissions ─────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_permissions (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        description TEXT,
        category VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_permissions_category ON chatbot_permissions(category)",

    # ── 007: chatbot_role_permissions ────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_role_permissions (
        id SERIAL PRIMARY KEY,
        role_id INTEGER NOT NULL REFERENCES chatbot_roles(id) ON DELETE CASCADE,
        permission_id INTEGER NOT NULL REFERENCES chatbot_permissions(id) ON DELETE CASCADE,
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(role_id, permission_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_role_permissions_role ON chatbot_role_permissions(role_id)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_role_permissions_permission ON chatbot_role_permissions(permission_id)",

    # ── 007: chatbot_user_groups ─────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_user_groups (
        id SERIAL PRIMARY KEY,
        chatbot_user_id INTEGER NOT NULL REFERENCES chatbot_users(id) ON DELETE CASCADE,
        chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(chatbot_user_id, chatbot_group_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_user_groups_user ON chatbot_user_groups(chatbot_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_user_groups_group ON chatbot_user_groups(chatbot_group_id)",

    # ── 007: chatbot_group_roles ─────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_group_roles (
        id SERIAL PRIMARY KEY,
        chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
        chatbot_role_id INTEGER NOT NULL REFERENCES chatbot_roles(id) ON DELETE CASCADE,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(chatbot_group_id, chatbot_role_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_group_roles_group ON chatbot_group_roles(chatbot_group_id)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_group_roles_role ON chatbot_group_roles(chatbot_role_id)",

    # ── 007: chatbot_corpus_access ───────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_corpus_access (
        id SERIAL PRIMARY KEY,
        chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
        corpus_id INTEGER NOT NULL REFERENCES corpora(id) ON DELETE CASCADE,
        permission VARCHAR(50) NOT NULL DEFAULT 'query',
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        granted_by INTEGER REFERENCES users(id),
        UNIQUE(chatbot_group_id, corpus_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_corpus_access_group ON chatbot_corpus_access(chatbot_group_id)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_corpus_access_corpus ON chatbot_corpus_access(corpus_id)",

    # ── 007: chatbot_agent_access ────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_agent_access (
        id SERIAL PRIMARY KEY,
        chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
        agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
        can_use BOOLEAN DEFAULT TRUE,
        can_configure BOOLEAN DEFAULT FALSE,
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        granted_by INTEGER REFERENCES users(id),
        UNIQUE(chatbot_group_id, agent_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_agent_access_group ON chatbot_agent_access(chatbot_group_id)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_agent_access_agent ON chatbot_agent_access(agent_id)",

    # ── 007: chatbot_tool_access ─────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_tool_access (
        id SERIAL PRIMARY KEY,
        chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
        tool_name VARCHAR(255) NOT NULL,
        agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
        is_allowed BOOLEAN DEFAULT TRUE,
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        granted_by INTEGER REFERENCES users(id),
        UNIQUE(chatbot_group_id, tool_name, agent_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_tool_access_group ON chatbot_tool_access(chatbot_group_id)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_tool_access_tool ON chatbot_tool_access(tool_name)",

    # ── 009: chatbot_agents ──────────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_agents (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        display_name VARCHAR(255) NOT NULL,
        description TEXT,
        agent_type VARCHAR(100) NOT NULL,
        tools JSONB NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_agents_type ON chatbot_agents(agent_type)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_agents_active ON chatbot_agents(is_active)",

    # ── 009: chatbot_group_agents ────────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS chatbot_group_agents (
        id SERIAL PRIMARY KEY,
        group_id INTEGER REFERENCES chatbot_groups(id) ON DELETE CASCADE,
        agent_id INTEGER REFERENCES chatbot_agents(id) ON DELETE CASCADE,
        can_use BOOLEAN DEFAULT TRUE,
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        granted_by INTEGER REFERENCES users(id),
        UNIQUE(group_id, agent_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_group_agents_group ON chatbot_group_agents(group_id)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_group_agents_agent ON chatbot_group_agents(agent_id)",

    # ── 012: google_group_agent_mappings ─────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS google_group_agent_mappings (
        id SERIAL PRIMARY KEY,
        google_group_email VARCHAR(255) NOT NULL,
        chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
        priority INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER REFERENCES users(id),
        UNIQUE(google_group_email)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_gg_agent_map_email ON google_group_agent_mappings(google_group_email)",
    "CREATE INDEX IF NOT EXISTS idx_gg_agent_map_active ON google_group_agent_mappings(is_active)",

    # ── 012: google_group_corpus_mappings ────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS google_group_corpus_mappings (
        id SERIAL PRIMARY KEY,
        google_group_email VARCHAR(255) NOT NULL,
        corpus_id INTEGER NOT NULL REFERENCES corpora(id) ON DELETE CASCADE,
        permission VARCHAR(50) NOT NULL DEFAULT 'query',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER REFERENCES users(id),
        UNIQUE(google_group_email, corpus_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_gg_corpus_map_email ON google_group_corpus_mappings(google_group_email)",
    "CREATE INDEX IF NOT EXISTS idx_gg_corpus_map_corpus ON google_group_corpus_mappings(corpus_id)",
    "CREATE INDEX IF NOT EXISTS idx_gg_corpus_map_active ON google_group_corpus_mappings(is_active)",

    # ── 012: user_google_group_sync ──────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS user_google_group_sync (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        google_groups JSONB,
        last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sync_source VARCHAR(50) DEFAULT 'login',
        UNIQUE(user_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_gg_sync_user ON user_google_group_sync(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_gg_sync_time ON user_google_group_sync(last_synced_at)",

    # ── 008: document_access_log ─────────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS document_access_log (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        corpus_id INTEGER NOT NULL REFERENCES corpora(id) ON DELETE CASCADE,
        document_name VARCHAR(255) NOT NULL,
        document_file_id VARCHAR(255),
        access_type VARCHAR(50) DEFAULT 'view',
        success BOOLEAN NOT NULL,
        error_message TEXT,
        source_uri TEXT,
        ip_address VARCHAR(45),
        user_agent TEXT,
        accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS idx_document_access_user ON document_access_log(user_id, accessed_at)",
    "CREATE INDEX IF NOT EXISTS idx_document_access_corpus ON document_access_log(corpus_id, accessed_at)",
    "CREATE INDEX IF NOT EXISTS idx_document_access_time ON document_access_log(accessed_at)",
    "CREATE INDEX IF NOT EXISTS idx_document_access_success ON document_access_log(success, accessed_at)",

    # ── Extra columns that may be missing on older schemas ───────────────────
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255)",
    "ALTER TABLE corpora ADD COLUMN IF NOT EXISTS gcs_bucket VARCHAR(500)",
    "ALTER TABLE chatbot_users ADD COLUMN IF NOT EXISTS user_id INTEGER",
    "ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0",
    "ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS user_query_count INTEGER DEFAULT 0",

    # ── Fix column rename: vertex_ai_corpus_id → vertex_corpus_id ─────────
    # Older deploys created the column as vertex_ai_corpus_id; all code uses
    # vertex_corpus_id. Rename if the old name exists. Safe: fails silently
    # if the old column doesn't exist (caught by the per-statement try/except).
    "ALTER TABLE corpora RENAME COLUMN vertex_ai_corpus_id TO vertex_corpus_id",

    # ── Rollback migration 010: revert table/column renames ──────────────
    # Migration 010 renamed chatbot_roles → chatbot_agent_types (and similar)
    # on some databases (e.g. Develom). schema_init.py creates the original
    # names, and ALL Python code now uses the original names. These renames
    # bring migrated databases back in sync. Each statement fails silently on
    # databases that already use the original names.
    #
    # Tables: reverse the renames
    "ALTER TABLE chatbot_agent_types RENAME TO chatbot_roles",
    "ALTER TABLE chatbot_tools RENAME TO chatbot_permissions",
    "ALTER TABLE chatbot_agent_type_tools RENAME TO chatbot_role_permissions",
    "ALTER TABLE chatbot_group_agent_types RENAME TO chatbot_group_roles",
    # Columns: reverse the renames inside the (now-original-named) tables
    "ALTER TABLE chatbot_role_permissions RENAME COLUMN agent_type_id TO role_id",
    "ALTER TABLE chatbot_role_permissions RENAME COLUMN tool_id TO permission_id",
    "ALTER TABLE chatbot_group_roles RENAME COLUMN chatbot_agent_type_id TO chatbot_role_id",
]


def initialize_schema():
    """
    Initialize PostgreSQL database schema using self-contained DDL.

    Each statement is executed and committed individually so one failure
    doesn't cascade to the rest. All statements are idempotent
    (CREATE TABLE IF NOT EXISTS / ALTER TABLE ADD COLUMN IF NOT EXISTS).
    """
    import psycopg2
    from .connection import PG_CONFIG

    logger.info("Initializing PostgreSQL schema...")
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        conn.autocommit = False
        ok = 0
        skipped = 0
        try:
            cur = conn.cursor()
            for ddl in SCHEMA_DDL:
                label = ddl.strip().split('\n')[0][:70]
                try:
                    cur.execute(ddl)
                    conn.commit()
                    ok += 1
                except Exception as e:
                    conn.rollback()
                    err = str(e).split('\n')[0][:80]
                    logger.warning(f"⚠️  {label} — {err}")
                    skipped += 1
            cur.close()
            logger.info(f"✅ Database schema initialized successfully ({ok} ok, {skipped} skipped)")
        finally:
            conn.close()
    except Exception as e:
        logger.critical(
            f"❌ FATAL: Cannot connect to database — schema initialization failed: {e}\n"
            f"   Check DB_PASSWORD secret, CLOUD_SQL_CONNECTION_NAME, and Cloud SQL IAM permissions."
        )
        raise
