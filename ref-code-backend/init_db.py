#!/usr/bin/env python3
"""
Initialize PostgreSQL database schema for ADK Multi-Agents.
Run this script to create all necessary tables.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_schema():
    """Initialize database schema by running the SQL file."""
    
    # Read SQL file
    sql_file = os.path.join(os.path.dirname(__file__), 'init_postgresql_schema.sql')
    
    with open(sql_file, 'r') as f:
        sql_script = f.read()
    
    # Split by semicolons and execute each statement
    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
    
    logger.info(f"Executing {len(statements)} SQL statements...")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for i, statement in enumerate(statements, 1):
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                        logger.info(f"Statement {i}/{len(statements)} executed successfully")
                    except Exception as e:
                        logger.error(f"Error executing statement {i}: {e}")
                        logger.error(f"Statement: {statement[:100]}...")
                        raise
            
            conn.commit()
            logger.info("✅ Database schema initialized successfully!")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

if __name__ == "__main__":
    init_schema()
