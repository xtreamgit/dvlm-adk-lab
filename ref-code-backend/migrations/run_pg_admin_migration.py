#!/usr/bin/env python3
"""
PostgreSQL migration for admin tables.
This runs automatically on container startup.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from database.connection import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_admin_tables_migration():
    """Create admin tables if they don't exist."""
    
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
    """
    
    index_sql = """
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
            
            # Check if tables already exist
            cursor.execute("""
                SELECT COUNT(*) as count FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'corpus_metadata'
            """)
            result = cursor.fetchone()
            if result and (result['count'] if isinstance(result, dict) else result[0]) > 0:
                logger.info("⏭️  corpus_metadata table already exists, skipping migration")
                return
            
            # Execute table creation - one at a time with error handling
            tables = [
                ("corpus_audit_log", """
                    CREATE TABLE corpus_audit_log (
                        id SERIAL PRIMARY KEY,
                        corpus_id INTEGER,
                        user_id INTEGER,
                        action VARCHAR(50) NOT NULL,
                        changes JSONB,
                        metadata JSONB,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                    )
                """),
                ("corpus_metadata", """
                    CREATE TABLE corpus_metadata (
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
                    )
                """),
                ("corpus_sync_schedule", """
                    CREATE TABLE corpus_sync_schedule (
                        id SERIAL PRIMARY KEY,
                        corpus_id INTEGER,
                        frequency VARCHAR(50),
                        last_run TIMESTAMP,
                        next_run TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE
                    )
                """)
            ]
            
            for table_name, create_sql in tables:
                try:
                    logger.info(f"Creating table: {table_name}")
                    cursor.execute(create_sql)
                except Exception as e:
                    logger.warning(f"Table {table_name} error (may exist): {e}")
            
            # Execute indexes
            index_statements = [s.strip() for s in index_sql.split(';') if s.strip()]
            for statement in index_statements:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")
            
            conn.commit()
            logger.info("✅ Admin tables migration completed successfully")
            
    except Exception as e:
        logger.error(f"Admin tables migration error: {e}", exc_info=True)
        # Don't fail startup if tables already exist

if __name__ == '__main__':
    run_admin_tables_migration()
