#!/usr/bin/env python3
"""Test the /me/available-agents endpoint"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5433')),
    'database': os.getenv('DB_NAME', 'adk_agents_db_dev'),
    'user': os.getenv('DB_USER', 'adk_dev_user'),
    'password': os.getenv('DB_PASSWORD', 'dev_password_123')
}

def test_query():
    """Test the query that the endpoint uses"""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Test with alice username
        username = 'alice'
        
        print(f"Testing with username: {username}")
        print("-" * 60)
        
        # First query: Get chatbot_user_id
        cur.execute("""
            SELECT id FROM chatbot_users WHERE username = %s
        """, (username,))
        chatbot_user = cur.fetchone()
        
        if not chatbot_user:
            print(f"❌ No chatbot_user found for username: {username}")
            return
        
        print(f"✅ Found chatbot_user_id: {chatbot_user['id']}")
        
        # Second query: Get available agents
        cur.execute("""
            SELECT DISTINCT a.id, a.name, a.display_name, a.description, 
                   a.agent_type, a.tools, a.is_active, a.created_at
            FROM chatbot_agents a
            JOIN chatbot_group_agents ga ON a.id = ga.agent_id
            JOIN chatbot_user_groups ug ON ga.group_id = ug.chatbot_group_id
            WHERE ug.chatbot_user_id = %s 
              AND a.is_active = TRUE 
              AND ga.can_use = TRUE
            ORDER BY a.id
        """, (chatbot_user['id'],))
        agents = cur.fetchall()
        
        print(f"\n✅ Found {len(agents)} available agent(s):")
        for agent in agents:
            print(f"\n  Agent ID: {agent['id']}")
            print(f"  Name: {agent['name']}")
            print(f"  Display Name: {agent['display_name']}")
            print(f"  Type: {agent['agent_type']}")
            print(f"  Tools: {agent['tools']}")
            print(f"  Active: {agent['is_active']}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query()
