#!/usr/bin/env python3
"""
Seed agents directly into Cloud SQL PostgreSQL database.
"""

import psycopg2
from datetime import datetime, timezone
import os

# Cloud SQL connection settings
CLOUD_SQL_CONNECTION_NAME = "adk-rag-ma:us-west1:adk-multi-agents-db"
DB_USER = "adk_app_user"
DB_NAME = "adk_agents_db"
DB_PASSWORD = "YSdozFP2TnDM20mfwRRiQYIqGNZw7T/6WrSd+knD2aM="

# Agents to seed
AGENTS = [
    {
        "name": "default-agent",
        "display_name": "Default Agent",
        "config_path": "develom",
        "description": "Default general-purpose RAG agent"
    },
    {
        "name": "agent1",
        "display_name": "Agent 1",
        "config_path": "agent1",
        "description": "Specialized agent 1"
    },
    {
        "name": "agent2",
        "display_name": "Agent 2",
        "config_path": "agent2",
        "description": "Specialized agent 2"
    },
    {
        "name": "agent3",
        "display_name": "Agent 3",
        "config_path": "agent3",
        "description": "Specialized agent 3"
    }
]


def seed_agents():
    """Seed agents into Cloud SQL PostgreSQL."""
    print("Connecting to Cloud SQL PostgreSQL...")
    
    # Connect via Unix socket for Cloud SQL Proxy
    conn = psycopg2.connect(
        host=f'/cloudsql/{CLOUD_SQL_CONNECTION_NAME}',
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    
    cursor = conn.cursor()
    created_count = 0
    skipped_count = 0
    
    print("\nSeeding agents...")
    
    for agent_data in AGENTS:
        try:
            # Check if agent exists
            cursor.execute(
                "SELECT id, name FROM agents WHERE name = %s",
                (agent_data["name"],)
            )
            existing = cursor.fetchone()
            
            if existing:
                print(f"⏭️  Agent '{agent_data['name']}' already exists (ID: {existing[0]})")
                skipped_count += 1
                continue
            
            # Create agent
            created_at = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                INSERT INTO agents (name, display_name, description, config_path, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                agent_data["name"],
                agent_data["display_name"],
                agent_data["description"],
                agent_data["config_path"],
                True,
                created_at
            ))
            
            agent_id = cursor.fetchone()[0]
            conn.commit()
            
            print(f"✅ Created agent: {agent_data['name']} (ID: {agent_id})")
            created_count += 1
            
        except Exception as e:
            print(f"❌ Failed to create agent '{agent_data['name']}': {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print("Agent Seeding Summary:")
    print(f"  Created: {created_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total: {len(AGENTS)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    seed_agents()
