#!/usr/bin/env python3
"""
Sync document counts from Vertex AI to database corpus_metadata table.
This fixes the issue where admin panel shows 0 documents for all corpora.
"""

import os
import sys
import logging
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def sync_document_counts(db_host=None, db_port=None, db_name=None, db_user=None, db_password=None):
    """
    Sync document counts from Vertex AI to database.
    
    Args:
        db_host: Database host (default: from env or localhost)
        db_port: Database port (default: from env or 5433)
        db_name: Database name (default: from env or adk_agents_db_dev)
        db_user: Database user (default: from env or adk_dev_user)
        db_password: Database password (default: from env)
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Initialize Vertex AI
    try:
        import vertexai
        from vertexai import rag
        
        project_id = os.getenv('PROJECT_ID', 'adk-rag-ma')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-west1')
        
        logger.info(f"Initializing Vertex AI: project={project_id}, location={location}")
        vertexai.init(project=project_id, location=location)
        
    except Exception as e:
        logger.error(f"Failed to initialize Vertex AI: {e}")
        return False
    
    # Database connection params
    db_config = {
        'host': db_host or os.getenv('DB_HOST', 'localhost'),
        'port': db_port or int(os.getenv('DB_PORT', '5433')),
        'database': db_name or os.getenv('DB_NAME', 'adk_agents_db_dev'),
        'user': db_user or os.getenv('DB_USER', 'adk_dev_user'),
        'password': db_password or os.getenv('DB_PASSWORD', 'dev_password_123')
    }
    
    logger.info(f"Connecting to database: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    try:
        conn = psycopg2.connect(**db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # Get all corpora from database
        cursor.execute("""
            SELECT c.id, c.name, c.vertex_corpus_id, c.is_active
            FROM corpora c
            WHERE c.vertex_corpus_id IS NOT NULL
            ORDER BY c.name
        """)
        
        corpora = cursor.fetchall()
        logger.info(f"Found {len(corpora)} corpora with vertex_corpus_id")
        
        updated_count = 0
        error_count = 0
        
        for corpus in corpora:
            corpus_id = corpus['id']
            corpus_name = corpus['name']
            vertex_corpus_id = corpus['vertex_corpus_id']
            
            try:
                # Fetch document count from Vertex AI
                logger.info(f"Fetching documents for '{corpus_name}' ({vertex_corpus_id})...")
                files = list(rag.list_files(corpus_name=vertex_corpus_id))
                doc_count = len(files)
                
                logger.info(f"  Found {doc_count} documents")
                
                # Update corpus_metadata
                cursor.execute("""
                    INSERT INTO corpus_metadata (corpus_id, document_count, last_document_count_update)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (corpus_id) 
                    DO UPDATE SET 
                        document_count = EXCLUDED.document_count,
                        last_document_count_update = EXCLUDED.last_document_count_update
                """, (corpus_id, doc_count, datetime.now()))
                
                conn.commit()
                updated_count += 1
                logger.info(f"✅ Updated '{corpus_name}': {doc_count} documents")
                
            except Exception as e:
                logger.error(f"❌ Failed to update '{corpus_name}': {e}")
                error_count += 1
                continue
        
        cursor.close()
        conn.close()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Sync complete: {updated_count} updated, {error_count} errors")
        logger.info("=" * 60)
        
        return error_count == 0
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync document counts from Vertex AI to database')
    parser.add_argument('--cloud', action='store_true', help='Sync to cloud database (requires Cloud SQL Proxy)')
    parser.add_argument('--host', help='Database host')
    parser.add_argument('--port', type=int, help='Database port')
    parser.add_argument('--database', help='Database name')
    parser.add_argument('--user', help='Database user')
    parser.add_argument('--password', help='Database password')
    
    args = parser.parse_args()
    
    if args.cloud:
        logger.info("Syncing to CLOUD database")
        logger.info("Make sure Cloud SQL Proxy is running on port 5434")
        logger.info("  cloud-sql-proxy adk-rag-ma:us-west1:adk-multi-agents-db --port 5434")
        logger.info("")
        
        # Cloud database defaults (via proxy)
        success = sync_document_counts(
            db_host=args.host or '127.0.0.1',
            db_port=args.port or 5434,
            db_name=args.database or 'adk_agents_db',
            db_user=args.user or 'adk_app_user',
            db_password=args.password or os.getenv('CLOUD_DB_PASSWORD')
        )
    else:
        logger.info("Syncing to LOCAL database")
        logger.info("")
        
        # Local database defaults
        success = sync_document_counts(
            db_host=args.host,
            db_port=args.port,
            db_name=args.database,
            db_user=args.user,
            db_password=args.password
        )
    
    sys.exit(0 if success else 1)
