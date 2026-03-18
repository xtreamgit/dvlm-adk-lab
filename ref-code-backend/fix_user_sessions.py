#!/usr/bin/env python3
"""
Fix user_sessions table - add missing message_count and user_query_count columns
Date: 2026-01-23
Issue: Chat UI failing with "column user_query_count does not exist"
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db_connection

def fix_user_sessions_schema():
    """Add missing columns to user_sessions table"""
    
    print("Fixing user_sessions table schema...")
    print("=" * 80)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Add message_count column
        print("\n1. Adding message_count column...")
        try:
            cursor.execute("""
                ALTER TABLE user_sessions 
                ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0
            """)
            conn.commit()
            print("   ✅ message_count column added")
        except Exception as e:
            print(f"   ⚠️  message_count: {e}")
        
        # Add user_query_count column
        print("\n2. Adding user_query_count column...")
        try:
            cursor.execute("""
                ALTER TABLE user_sessions 
                ADD COLUMN IF NOT EXISTS user_query_count INTEGER DEFAULT 0
            """)
            conn.commit()
            print("   ✅ user_query_count column added")
        except Exception as e:
            print(f"   ⚠️  user_query_count: {e}")
        
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
            col_dict = dict(col)
            print(f"   - {col_dict['column_name']:20} {col_dict['data_type']:15} "
                  f"default={col_dict['column_default'] or 'NULL':20} "
                  f"nullable={col_dict['is_nullable']}")
        
        # Check if required columns exist
        column_names = [dict(col)['column_name'] for col in columns]
        required = ['message_count', 'user_query_count']
        missing = [col for col in required if col not in column_names]
        
        if missing:
            print(f"\n   ❌ Still missing columns: {missing}")
            return False
        else:
            print(f"\n   ✅ All required columns present!")
            return True

if __name__ == "__main__":
    try:
        success = fix_user_sessions_schema()
        print("\n" + "=" * 80)
        if success:
            print("✅ Schema fix completed successfully!")
            sys.exit(0)
        else:
            print("❌ Schema fix failed - missing columns")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
