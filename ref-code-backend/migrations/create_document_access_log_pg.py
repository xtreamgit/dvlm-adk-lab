#!/usr/bin/env python3
"""
PostgreSQL migration to create document_access_log table.
Run this to create the missing table in Cloud SQL.
"""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from database.connection import get_db_connection, DB_TYPE
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_document_access_log_table():
    """Create document_access_log table in PostgreSQL."""
    
    if DB_TYPE != 'postgresql':
        logger.info("Skipping - not using PostgreSQL")
        return
    
    migration_sql = """
    -- Create document_access_log table
    CREATE TABLE IF NOT EXISTS document_access_log (
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
    );

    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_document_access_user ON document_access_log(user_id, accessed_at);
    CREATE INDEX IF NOT EXISTS idx_document_access_corpus ON document_access_log(corpus_id, accessed_at);
    CREATE INDEX IF NOT EXISTS idx_document_access_time ON document_access_log(accessed_at);
    CREATE INDEX IF NOT EXISTS idx_document_access_success ON document_access_log(success, accessed_at);
    """
    
    try:
        logger.info("Creating document_access_log table in PostgreSQL...")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Execute the migration
            cursor.execute(migration_sql)
            conn.commit()
            
            logger.info("✅ document_access_log table created successfully")
            
            # Verify table exists
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'document_access_log'
            """)
            result = cursor.fetchone()
            
            if result:
                logger.info(f"✅ Verified: {result['table_name']} table exists")
            else:
                logger.error("❌ Table creation verification failed")
                
    except Exception as e:
        logger.error(f"❌ Failed to create document_access_log table: {e}")
        raise


if __name__ == "__main__":
    create_document_access_log_table()
