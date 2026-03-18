"""
Agent repository for database operations.
"""

from typing import Optional, List, Dict
from datetime import datetime, timezone

from ..connection import get_db_connection


class AgentRepository:
    """Repository for agent-related database operations."""
    
    @staticmethod
    def get_by_id(agent_id: int) -> Optional[Dict]:
        """Get agent by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE id = %s", (agent_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_by_name(name: str) -> Optional[Dict]:
        """Get agent by name."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE name = %s", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_by_config_path(config_path: str) -> Optional[Dict]:
        """Get agent by config path."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE config_path = %s", (config_path,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def create(name: str, display_name: str, config_path: str, 
              description: Optional[str] = None) -> Dict:
        """Create a new agent."""
        created_at = datetime.now(timezone.utc).isoformat()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agents (name, display_name, description, config_path, 
                                   is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (name, display_name, description, config_path, True, created_at))
            result = cursor.fetchone()
            agent_id = result['id'] if isinstance(result, dict) else result[0]
            conn.commit()
        
        return AgentRepository.get_by_id(agent_id)
    
    @staticmethod
    def get_all(active_only: bool = True) -> List[Dict]:
        """Get all agents."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM agents WHERE is_active = TRUE ORDER BY display_name")
            else:
                cursor.execute("SELECT * FROM agents ORDER BY display_name")
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(agent_id: int, **kwargs) -> Optional[Dict]:
        """Update agent fields."""
        if not kwargs:
            return AgentRepository.get_by_id(agent_id)
        
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        values = list(kwargs.values()) + [agent_id]
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE agents SET {set_clause} WHERE id = %s", values)
            conn.commit()
        
        return AgentRepository.get_by_id(agent_id)
    
    # ========== User-Agent Access ==========
    
    @staticmethod
    def grant_access(user_id: int, agent_id: int) -> bool:
        """Grant user access to an agent."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_agent_access (user_id, agent_id)
                    VALUES (%s, %s)
                """, (user_id, agent_id))
                conn.commit()
            return True
        except Exception:
            return False
    
    @staticmethod
    def revoke_access(user_id: int, agent_id: int) -> bool:
        """Revoke user access to an agent."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM user_agent_access WHERE user_id = %s AND agent_id = %s
            """, (user_id, agent_id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def has_access(user_id: int, agent_id: int) -> bool:
        """Check if user has access to an agent."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM user_agent_access 
                WHERE user_id = %s AND agent_id = %s LIMIT 1
            """, (user_id, agent_id))
            return cursor.fetchone() is not None
    
    @staticmethod
    def get_user_agents(user_id: int, active_only: bool = True) -> List[Dict]:
        """Get all agents a user has access to."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT a.* FROM agents a
                JOIN user_agent_access uaa ON a.id = uaa.agent_id
                WHERE uaa.user_id = %s
            """
            if active_only:
                query += " AND a.is_active = TRUE"
            query += " ORDER BY a.display_name"
            
            cursor.execute(query, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_agent_users(agent_id: int) -> List[int]:
        """Get all user IDs that have access to an agent."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id FROM user_agent_access WHERE agent_id = %s
            """, (agent_id,))
            return [row['user_id'] for row in cursor.fetchall()]
