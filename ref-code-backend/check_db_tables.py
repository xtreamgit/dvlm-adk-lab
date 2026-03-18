"""Check PostgreSQL database tables."""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db_connection, DB_TYPE

print(f"Database Type: {DB_TYPE}")

if DB_TYPE != "postgresql":
    print("Not using PostgreSQL")
    sys.exit(0)

try:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table[0]}")
                
            # Check users table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            if columns:
                print(f"\n📋 Users table structure:")
                for col in columns:
                    print(f"   - {col[0]}: {col[1]}")
        else:
            print("\n❌ No tables found in database!")
            
except Exception as e:
    print(f"\n❌ Error connecting to database: {e}")
    import traceback
    traceback.print_exc()
