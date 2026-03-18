#!/usr/bin/env python3
"""
Add missing columns to corpus_metadata table.
This runs as part of startup to ensure the table has all required columns.
"""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def add_missing_columns():
    """Add missing columns to corpus_metadata if they don't exist."""
    
    logger.info("[ADD_COLUMNS] Checking corpus_metadata schema...")
    
    # Retry logic for Cloud SQL connection (socket may not be ready immediately)
    max_retries = 5
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            return _add_columns_with_connection()
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"[ADD_COLUMNS] Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                logger.info(f"[ADD_COLUMNS] Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"[ADD_COLUMNS] All {max_retries} connection attempts failed")
                logger.error(f"[ADD_COLUMNS] Error: {e}", exc_info=True)
                # Don't fail startup - just log the error
                logger.warning("[ADD_COLUMNS] Skipping column additions - will retry on next startup")
                return True  # Return True to not block startup

def _add_columns_with_connection():
    """Internal method that performs the actual column additions."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'corpus_metadata'
                )
            """)
            result = cursor.fetchone()
            table_exists = result[0] if isinstance(result, tuple) else result['exists']
            
            if not table_exists:
                logger.info("[ADD_COLUMNS] corpus_metadata table doesn't exist, will be created by other migration")
                return True
            
            # Define columns to add
            columns_to_add = [
                ('created_by', 'INTEGER', 'FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL'),
                ('last_synced_at', 'TIMESTAMP', None),
                ('last_synced_by', 'INTEGER', 'FOREIGN KEY (last_synced_by) REFERENCES users(id) ON DELETE SET NULL'),
                ('document_count', 'INTEGER DEFAULT 0', None),
                ('last_document_count_update', 'TIMESTAMP', None),
                ('sync_status', "VARCHAR(50) DEFAULT 'active'", None),
                ('sync_error_message', 'TEXT', None),
                ('tags', 'JSONB', None),
                ('notes', 'TEXT', None),
            ]
            
            added_count = 0
            for column_name, column_type, constraint in columns_to_add:
                # Check if column exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'corpus_metadata' 
                        AND column_name = %s
                    )
                """, (column_name,))
                result = cursor.fetchone()
                column_exists = result[0] if isinstance(result, tuple) else result['exists']
                
                if not column_exists:
                    logger.info(f"[ADD_COLUMNS] Adding column: {column_name}")
                    try:
                        cursor.execute(f"ALTER TABLE corpus_metadata ADD COLUMN {column_name} {column_type}")
                        if constraint:
                            cursor.execute(f"ALTER TABLE corpus_metadata ADD {constraint}")
                        added_count += 1
                        logger.info(f"[ADD_COLUMNS] ✅ Added {column_name}")
                    except Exception as e:
                        logger.warning(f"[ADD_COLUMNS] Failed to add {column_name}: {e}")
            
            conn.commit()
            
            if added_count > 0:
                logger.info(f"[ADD_COLUMNS] ✅ Added {added_count} columns successfully")
            else:
                logger.info("[ADD_COLUMNS] ✅ All columns already exist")
            
            # Verify the columns now exist
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'corpus_metadata'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            column_names = [c[0] if isinstance(c, tuple) else c['column_name'] for c in columns]
            logger.info(f"[ADD_COLUMNS] Final columns: {column_names}")
            
            return True
            
    except Exception as e:
        logger.error(f"[ADD_COLUMNS] Error: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    success = add_missing_columns()
    sys.exit(0 if success else 1)
