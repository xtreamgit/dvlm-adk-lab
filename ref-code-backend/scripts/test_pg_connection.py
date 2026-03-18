#!/usr/bin/env python3
"""
Test PostgreSQL connection from backend code.
"""
import os
import sys

# Set environment variables for PostgreSQL
os.environ['DB_TYPE'] = 'postgresql'
os.environ['DB_HOST'] = '34.53.74.180'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'adk_agents_db'
os.environ['DB_USER'] = 'adk_app_user'
os.environ['DB_PASSWORD'] = os.environ.get('DB_PASSWORD', '')

if not os.environ['DB_PASSWORD']:
    print("❌ DB_PASSWORD environment variable not set")
    print("   Set it with: export DB_PASSWORD=your_password")
    sys.exit(1)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print("🔌 Testing PostgreSQL Connection")
print("=" * 50)
print()

try:
    from database.connection import init_database, execute_query
    
    print("1. Initializing database connection...")
    init_database()
    print("   ✅ Database initialized\n")
    
    print("2. Testing query execution...")
    users = execute_query("SELECT COUNT(*) as count FROM users")
    print(f"   ✅ Users in database: {users[0]['count']}\n")
    
    print("3. Fetching sample data...")
    sample_users = execute_query("SELECT username, email FROM users LIMIT 3")
    print("   ✅ Sample users:")
    for user in sample_users:
        print(f"      - {user['username']} ({user['email']})")
    print()
    
    print("4. Testing groups...")
    groups = execute_query("SELECT name FROM groups ORDER BY name")
    print(f"   ✅ Groups ({len(groups)}):")
    for group in groups:
        print(f"      - {group['name']}")
    print()
    
    print("5. Testing corpora...")
    corpora = execute_query("SELECT name FROM corpora WHERE is_active = TRUE ORDER BY name")
    print(f"   ✅ Active corpora ({len(corpora)}):")
    for corpus in corpora:
        print(f"      - {corpus['name']}")
    print()
    
    print("=" * 50)
    print("✅ PostgreSQL connection test PASSED")
    print("=" * 50)
    
except Exception as e:
    print(f"\n❌ Connection test FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
