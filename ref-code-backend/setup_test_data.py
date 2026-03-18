"""
Setup test data for agent type hierarchy testing

Creates:
1. Chatbot user for 'alice'
2. Chatbot group 'Test Contributors'
3. Agent type 'contributor' (if not exists)
4. Assigns alice to the group
5. Assigns contributor agent type to the group
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db_connection

def setup_test_data():
    """Setup test data for alice with contributor agent type"""
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            print("🔧 Setting up test data for agent type hierarchy...\n")
            
            # Step 1: Check if alice exists as a regular user
            cur.execute("SELECT id, username FROM users WHERE username = 'alice'")
            user = cur.fetchone()
            if user:
                print(f"✅ Found regular user 'alice' (id: {user['id']})")
            else:
                print("❌ Regular user 'alice' not found")
                return
            
            # Step 2: Create or get chatbot user for alice
            cur.execute("""
                INSERT INTO chatbot_users (username, email, full_name, is_active, created_by)
                VALUES ('alice', 'alice@example.com', 'Alice Test User', TRUE, %s)
                ON CONFLICT (username) DO UPDATE SET is_active = TRUE
                RETURNING id, username
            """, (user['id'],))
            chatbot_user = cur.fetchone()
            print(f"✅ Chatbot user 'alice' ready (id: {chatbot_user['id']})")
            
            # Step 3: Create agent types if they don't exist
            agent_types = [
                ('viewer', 'Read-only access for general users'),
                ('contributor', 'Users who can add content'),
                ('content-manager', 'Manage documents within existing corpora'),
                ('corpus-manager', 'Full corpus lifecycle management')
            ]
            
            print("\n📋 Creating agent types...")
            for name, description in agent_types:
                cur.execute("""
                    INSERT INTO chatbot_roles (name, description, created_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) DO NOTHING
                    RETURNING id, name
                """, (name, description, user['id']))
                result = cur.fetchone()
                if result:
                    print(f"   ✅ Created agent type: {result['name']} (id: {result['id']})")
                else:
                    cur.execute("SELECT id, name FROM chatbot_roles WHERE name = %s", (name,))
                    result = cur.fetchone()
                    print(f"   ℹ️  Agent type exists: {result['name']} (id: {result['id']})")
            
            # Step 4: Create chatbot group
            cur.execute("""
                INSERT INTO chatbot_groups (name, description, is_active, created_by)
                VALUES ('Test Contributors', 'Test group for contributor agent type', TRUE, %s)
                ON CONFLICT (name) DO UPDATE SET is_active = TRUE
                RETURNING id, name
            """, (user['id'],))
            group = cur.fetchone()
            print(f"\n✅ Chatbot group ready: {group['name']} (id: {group['id']})")
            
            # Step 5: Get contributor agent type
            cur.execute("SELECT id FROM chatbot_roles WHERE name = 'contributor'")
            contributor_type = cur.fetchone()
            
            # Step 6: Assign alice to the group
            cur.execute("""
                INSERT INTO chatbot_user_groups (chatbot_user_id, chatbot_group_id)
                VALUES (%s, %s)
                ON CONFLICT (chatbot_user_id, chatbot_group_id) DO NOTHING
            """, (chatbot_user['id'], group['id']))
            print(f"✅ Assigned alice to group '{group['name']}'")
            
            # Step 7: Assign contributor agent type to the group
            cur.execute("""
                INSERT INTO chatbot_group_roles (chatbot_group_id, chatbot_role_id)
                VALUES (%s, %s)
                ON CONFLICT (chatbot_group_id, chatbot_role_id) DO NOTHING
            """, (group['id'], contributor_type['id']))
            print(f"✅ Assigned 'contributor' agent type to group '{group['name']}'")
            
            conn.commit()
            
            # Verify the setup
            print("\n" + "="*70)
            print("🔍 Verifying setup...")
            print("="*70)
            
            cur.execute("""
                SELECT 
                    cu.username,
                    cg.name as group_name,
                    cat.name as agent_type
                FROM chatbot_users cu
                JOIN chatbot_user_groups cug ON cu.id = cug.chatbot_user_id
                JOIN chatbot_groups cg ON cug.chatbot_group_id = cg.id
                JOIN chatbot_group_roles cgat ON cg.id = cgat.chatbot_group_id
                JOIN chatbot_roles cat ON cgat.chatbot_role_id = cat.id
                WHERE cu.username = 'alice'
            """)
            
            results = cur.fetchall()
            if results:
                print("\n✅ Setup verified successfully!")
                for row in results:
                    print(f"\n   User: {row['username']}")
                    print(f"   Group: {row['group_name']}")
                    print(f"   Agent Type: {row['agent_type']}")
                    
                # Show tools available
                print("\n📦 Tools available to alice (contributor):")
                tools = ['rag_query', 'list_corpora', 'get_corpus_info', 'browse_documents', 'add_data']
                for tool in tools:
                    print(f"   • {tool}")
            else:
                print("❌ Verification failed - no assignments found")
            
            print("\n" + "="*70)
            print("✅ Test data setup complete!")
            print("="*70)

if __name__ == "__main__":
    try:
        setup_test_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
