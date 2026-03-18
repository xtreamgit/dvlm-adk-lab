#!/usr/bin/env python3
"""
Migration script to add admin panel tables to PostgreSQL database.
Run this to add corpus_metadata, corpus_audit_log, and other admin tables.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the admin tables migration."""
    
    migration_sql = """
    -- Audit log for all corpus changes
    CREATE TABLE IF NOT EXISTS corpus_audit_log (
        id SERIAL PRIMARY KEY,
        corpus_id INTEGER,
        user_id INTEGER,
        action VARCHAR(50) NOT NULL,
        changes JSONB,
        metadata JSONB,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );

    -- Enhanced corpus metadata
    CREATE TABLE IF NOT EXISTS corpus_metadata (
        id SERIAL PRIMARY KEY,
        corpus_id INTEGER UNIQUE NOT NULL,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_synced_at TIMESTAMP,
        last_synced_by INTEGER,
        document_count INTEGER DEFAULT 0,
        last_document_count_update TIMESTAMP,
        sync_status VARCHAR(50) DEFAULT 'active',
        sync_error_message TEXT,
        tags JSONB,
        notes TEXT,
        FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (last_synced_by) REFERENCES users(id) ON DELETE SET NULL
    );

    -- Scheduled sync jobs
    CREATE TABLE IF NOT EXISTS corpus_sync_schedule (
        id SERIAL PRIMARY KEY,
        corpus_id INTEGER,
        frequency VARCHAR(50),
        last_run TIMESTAMP,
        next_run TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_audit_corpus ON corpus_audit_log(corpus_id);
    CREATE INDEX IF NOT EXISTS idx_audit_user ON corpus_audit_log(user_id);
    CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON corpus_audit_log(timestamp);
    CREATE INDEX IF NOT EXISTS idx_audit_action ON corpus_audit_log(action);
    CREATE INDEX IF NOT EXISTS idx_corpus_metadata_corpus ON corpus_metadata(corpus_id);
    CREATE INDEX IF NOT EXISTS idx_corpus_metadata_status ON corpus_metadata(sync_status);
    CREATE INDEX IF NOT EXISTS idx_sync_schedule_corpus ON corpus_sync_schedule(corpus_id);
    CREATE INDEX IF NOT EXISTS idx_sync_schedule_active ON corpus_sync_schedule(is_active);
    """
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Execute each statement
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
            
            for statement in statements:
                logger.info(f"Executing: {statement[:100]}...")
                cursor.execute(statement)
            
            conn.commit()
            logger.info("✅ Migration completed successfully!")
            
            # Verify tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('corpus_metadata', 'corpus_audit_log', 'corpus_sync_schedule')
            """)
            tables = cursor.fetchall()
            logger.info(f"✅ Created tables: {[t['table_name'] if isinstance(t, dict) else t[0] for t in tables]}")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    logger.info("Starting admin tables migration...")
    run_migration()
    logger.info("Migration complete!")
