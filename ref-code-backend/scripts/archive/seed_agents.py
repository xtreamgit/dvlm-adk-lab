"""
Auto-seed agents into database on startup.
"""

import logging
from datetime import datetime, timezone
from .connection import get_db_connection

logger = logging.getLogger(__name__)

# PostgreSQL placeholder
PLACEHOLDER = "%s"

# Default agents to seed
DEFAULT_AGENTS = [
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


def seed_default_agents():
    """
    Seed default agents into database if they don't exist.
    Safe to call on every startup - will skip existing agents.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            created_count = 0
            skipped_count = 0
            
            for agent_data in DEFAULT_AGENTS:
                try:
                    # Check if agent exists
                    cursor.execute(
                        f"SELECT id FROM agents WHERE name = {PLACEHOLDER}",
                        (agent_data["name"],)
                    )
                    existing = cursor.fetchone()
                    
                    if existing:
                        logger.debug(f"Agent '{agent_data['name']}' already exists")
                        skipped_count += 1
                        continue
                    
                    # Create agent
                    created_at = datetime.now(timezone.utc).isoformat()
                    cursor.execute(
                        f"""
                        INSERT INTO agents (name, display_name, description, config_path, is_active, created_at)
                        VALUES (%%s{PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
                        """,
                        (
                            agent_data["name"],
                            agent_data["display_name"],
                            agent_data["description"],
                            agent_data["config_path"],
                            True,
                            created_at
                        )
                    )
                    conn.commit()
                    
                    logger.info(f"✅ Auto-seeded agent: {agent_data['name']}")
                    created_count += 1
                    
                except Exception as e:
                    conn.rollback()
                    logger.warning(f"Could not seed agent '{agent_data['name']}': {e}")
            
            if created_count > 0:
                logger.info(f"✅ Auto-seeded {created_count} agent(s)")
            elif skipped_count > 0:
                logger.debug(f"All {skipped_count} default agents already exist")
                
    except Exception as e:
        logger.warning(f"Agent auto-seeding skipped: {e}")
