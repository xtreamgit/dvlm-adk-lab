"""
Run the agent access control migration.
This script creates the chatbot_agents and chatbot_group_agents tables,
seeds the 4 agent types, creates the 4 groups, and assigns agents to groups.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db_connection

def run_migration():
    """Execute the agent access control migration."""
    
    migration_file = 'src/database/migrations/009_agent_access_control.sql'
    
    print(f"📋 Running migration: {migration_file}")
    
    # Read the migration file
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    # Execute the migration
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Execute the entire migration
            cursor.execute(sql_content)
            conn.commit()
            
            print("✅ Migration completed successfully!")
            
            # Verify the results
            print("\n📊 Verifying migration results...")
            
            # Check agents
            cursor.execute("SELECT name, display_name, agent_type FROM chatbot_agents ORDER BY id")
            agents = cursor.fetchall()
            print(f"\n✅ Created {len(agents)} agents:")
            for agent in agents:
                print(f"   - {agent['display_name']} ({agent['name']}) - Type: {agent['agent_type']}")
            
            # Check groups
            cursor.execute("SELECT name, description FROM chatbot_groups WHERE name LIKE %s ORDER BY id", ('%-group',))
            groups = cursor.fetchall()
            print(f"\n✅ Created {len(groups)} groups:")
            for group in groups:
                print(f"   - {group['name']}: {group['description']}")
            
            # Check group-agent assignments
            cursor.execute("""
                SELECT g.name as group_name, a.display_name as agent_name
                FROM chatbot_group_agents ga
                JOIN chatbot_groups g ON ga.group_id = g.id
                JOIN chatbot_agents a ON ga.agent_id = a.id
                ORDER BY g.name
            """)
            assignments = cursor.fetchall()
            print(f"\n✅ Created {len(assignments)} group-agent assignments:")
            for assignment in assignments:
                print(f"   - {assignment['group_name']} → {assignment['agent_name']}")
            
            # Show tool configurations
            print("\n🔧 Agent Tool Configurations:")
            cursor.execute("SELECT display_name, tools FROM chatbot_agents ORDER BY id")
            agents_tools = cursor.fetchall()
            for agent in agents_tools:
                tools = agent['tools']
                print(f"\n   {agent['display_name']}:")
                for tool in tools:
                    print(f"      • {tool}")
            
            print("\n✨ Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_migration()
