"""
Debug script to test the user available agents query directly.
This will help identify the SQL error causing the 500 response.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db_connection

def debug_user_agents(user_id):
    """Debug the user available agents query"""
    
    print(f"🔍 Debugging user available agents for user_id: {user_id}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # First, check if the user exists and get their groups
        print("\n1️⃣ Checking user and their groups...")
        cursor.execute("""
            SELECT cu.id, cu.username, cu.full_name
            FROM chatbot_users cu
            WHERE cu.id = %s
        """, (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User {user_id} not found!")
            return
        
        print(f"✅ User found: {user['username']} ({user['full_name']})")
        
        # Get user's groups
        cursor.execute("""
            SELECT g.id, g.name
            FROM chatbot_groups g
            JOIN chatbot_user_groups ug ON g.id = ug.chatbot_group_id
            WHERE ug.chatbot_user_id = %s
        """, (user_id,))
        groups = cursor.fetchall()
        
        print(f"\n2️⃣ User belongs to {len(groups)} group(s):")
        for group in groups:
            print(f"   - {group['name']} (ID: {group['id']})")
        
        if not groups:
            print("⚠️ User has no groups assigned!")
            return
        
        # Check agents assigned to those groups
        print("\n3️⃣ Checking agents assigned to user's groups...")
        for group in groups:
            cursor.execute("""
                SELECT a.id, a.name, a.display_name
                FROM chatbot_agents a
                JOIN chatbot_group_agents ga ON a.id = ga.agent_id
                WHERE ga.group_id = %s AND ga.can_use = TRUE
            """, (group['id'],))
            agents = cursor.fetchall()
            
            print(f"\n   Group '{group['name']}' has {len(agents)} agent(s):")
            for agent in agents:
                print(f"      - {agent['display_name']} (ID: {agent['id']})")
        
        # Now try the full query that's failing
        print("\n4️⃣ Testing the full query...")
        try:
            cursor.execute("""
                SELECT DISTINCT a.id, a.name, a.display_name, a.description, 
                       a.agent_type, a.tools, a.is_active, a.created_at
                FROM chatbot_agents a
                JOIN chatbot_group_agents ga ON a.id = ga.agent_id
                JOIN chatbot_user_groups ug ON ga.group_id = ug.chatbot_group_id
                WHERE ug.chatbot_user_id = %s 
                  AND a.is_active = TRUE 
                  AND ga.can_use = TRUE
                ORDER BY a.id
            """, (user_id,))
            agents = cursor.fetchall()
            
            print(f"✅ Query successful! Found {len(agents)} agent(s):")
            for agent in agents:
                print(f"   - {agent['display_name']} ({agent['agent_type']})")
                print(f"     Tools: {agent['tools']}")
                
        except Exception as e:
            print(f"❌ Query failed with error:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    # Test with user ID 20 (from the test output)
    debug_user_agents(20)
