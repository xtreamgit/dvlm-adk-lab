#!/usr/bin/env python3
"""
Fix user_sessions table in Cloud SQL PostgreSQL
Add missing message_count and user_query_count columns
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Cloud SQL connection parameters
DB_HOST = os.getenv('DB_HOST', '/cloudsql/adk-rag-ma:us-west1:adk-multi-agents-db')
DB_NAME = os.getenv('DB_NAME', 'adk_agents_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

def fix_user_sessions_schema():
    """Add missing columns to user_sessions table"""
    
    print("Fixing user_sessions table in Cloud SQL...")
    print("=" * 80)
    print(f"Database: {DB_NAME}")
    print(f"Host: {DB_HOST}")
    print(f"User: {DB_USER}")
    print()
    
    # Connect to Cloud SQL
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    try:
        cursor = conn.cursor()
        
        # Add message_count column
        print("1. Adding message_count column...")
        cursor.execute("""
            ALTER TABLE user_sessions 
            ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0
        """)
        conn.commit()
        print("   ✅ message_count column added")
        
        # Add user_query_count column  
        print("\n2. Adding user_query_count column...")
        cursor.execute("""
            ALTER TABLE user_sessions 
            ADD COLUMN IF NOT EXISTS user_query_count INTEGER DEFAULT 0
        """)
        conn.commit()
        print("   ✅ user_query_count column added")
        
        # Verify the schema
        print("\n3. Verifying user_sessions schema...")
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'user_sessions'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("\n   Current columns:")
        for col in columns:
            print(f"   - {col[0]:20} {col[1]:15} default={col[2] or 'NULL':20} nullable={col[3]}")
        
        # Check if required columns exist
        column_names = [col[0] for col in columns]
        required = ['message_count', 'user_query_count']
        missing = [col for col in required if col not in column_names]
        
        if missing:
            print(f"\n   ❌ Still missing columns: {missing}")
            return False
        else:
            print(f"\n   ✅ All required columns present!")
            return True
            
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    try:
        success = fix_user_sessions_schema()
        print("\n" + "=" * 80)
        if success:
            print("✅ Schema fix completed successfully!")
            sys.exit(0)
        else:
            print("❌ Schema fix failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
