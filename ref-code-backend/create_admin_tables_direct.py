#!/usr/bin/env python3
"""
Direct SQL execution to create admin tables.
Run this via Cloud Run Jobs or as a one-time script.
"""

import os
import psycopg2

# Cloud SQL configuration
PG_CONFIG = {
    'host': os.getenv('DB_HOST', '/cloudsql/' + os.getenv('CLOUD_SQL_CONNECTION_NAME', '')),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'adk_agents_db'),
    'user': os.getenv('DB_USER', 'adk_app_user'),
    'password': os.getenv('DB_PASSWORD', ''),
}

def create_tables():
    """Create admin tables directly."""
    print(f"Connecting to database: {PG_CONFIG['database']} at {PG_CONFIG['host']}")
    
    conn = psycopg2.connect(**PG_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Create corpus_audit_log
        print("Creating corpus_audit_log table...")
        cursor.execute("""
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
            )
        """)
        
        # Create corpus_metadata
        print("Creating corpus_metadata table...")
        cursor.execute("""
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
            )
        """)
        
        # Create corpus_sync_schedule
        print("Creating corpus_sync_schedule table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corpus_sync_schedule (
                id SERIAL PRIMARY KEY,
                corpus_id INTEGER,
                frequency VARCHAR(50),
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_corpus ON corpus_audit_log(corpus_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON corpus_audit_log(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON corpus_audit_log(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON corpus_audit_log(action)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_metadata_corpus ON corpus_metadata(corpus_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_metadata_status ON corpus_metadata(sync_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_schedule_corpus ON corpus_sync_schedule(corpus_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_schedule_active ON corpus_sync_schedule(is_active)")
        
        conn.commit()
        print("✅ All tables created successfully!")
        
        # Verify tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('corpus_metadata', 'corpus_audit_log', 'corpus_sync_schedule')
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"✅ Verified tables: {[t[0] for t in tables]}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    create_tables()
