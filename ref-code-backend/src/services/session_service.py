"""
Session service for managing user sessions with agent and corpus tracking.
"""

import json
import logging
from typing import Optional, List
from datetime import datetime, timedelta, timezone

from database.connection import get_db_connection
from models.session import SessionData, SessionCreate, SessionUpdate

logger = logging.getLogger(__name__)

SESSION_EXPIRE_HOURS = 24  # Default session expiration
SESSION_IDLE_HOURS = 2     # Idle timeout: sessions inactive for this long are closed


class SessionService:
    """Service for session operations."""
    
    @staticmethod
    def create_session(session_create: SessionCreate) -> SessionData:
        """
        Create a new session.
        
        Args:
            session_create: SessionCreate model with session data
            
        Returns:
            Created SessionData object
        """
        created_at = datetime.now(timezone.utc).isoformat()
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=SESSION_EXPIRE_HOURS)).isoformat()
        active_corpora_json = json.dumps(session_create.active_corpora) if session_create.active_corpora else None
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_sessions 
                (session_id, user_id, active_agent_id, active_corpora, 
                 created_at, last_activity, expires_at, is_active,
                 message_count, user_query_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session_create.session_id, session_create.user_id, 
                  session_create.active_agent_id, active_corpora_json,
                  created_at, created_at, expires_at, True,
                  0, 0))
            conn.commit()
            session_id_db = cursor.lastrowid
        
        logger.info(f"Session created: {session_create.session_id} for user {session_create.user_id}")
        return SessionService.get_session_by_session_id(session_create.session_id)
    
    @staticmethod
    def get_session_by_id(session_id: int) -> Optional[SessionData]:
        """Get session by database ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_sessions WHERE id = %s", (session_id,))
            row = cursor.fetchone()
            if row:
                session_dict = dict(row)
                # Parse JSON active_corpora
                if session_dict.get('active_corpora'):
                    try:
                        session_dict['active_corpora'] = json.loads(session_dict['active_corpora'])
                    except (json.JSONDecodeError, TypeError):
                        session_dict['active_corpora'] = []
                return SessionData(**session_dict)
            return None
    
    @staticmethod
    def get_session_by_session_id(session_id: str) -> Optional[SessionData]:
        """Get session by session_id string."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_sessions WHERE session_id = %s", (session_id,))
            row = cursor.fetchone()
            if row:
                session_dict = dict(row)
                # Parse JSON active_corpora
                if session_dict.get('active_corpora'):
                    try:
                        session_dict['active_corpora'] = json.loads(session_dict['active_corpora'])
                    except (json.JSONDecodeError, TypeError):
                        session_dict['active_corpora'] = []
                return SessionData(**session_dict)
            return None
    
    @staticmethod
    def update_session(session_id: str, session_update: SessionUpdate) -> Optional[SessionData]:
        """
        Update session information.
        
        Args:
            session_id: Session ID string
            session_update: SessionUpdate model with fields to update
            
        Returns:
            Updated SessionData object or None if not found
        """
        update_data = session_update.model_dump(exclude_unset=True)
        if not update_data:
            return SessionService.get_session_by_session_id(session_id)
        
        # Convert active_corpora list to JSON
        if 'active_corpora' in update_data and update_data['active_corpora'] is not None:
            update_data['active_corpora'] = json.dumps(update_data['active_corpora'])
        
        # Always update last_activity
        if 'last_activity' not in update_data:
            update_data['last_activity'] = datetime.now(timezone.utc).isoformat()
        
        # Build UPDATE query
        set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
        values = list(update_data.values()) + [session_id]
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE user_sessions SET {set_clause} WHERE session_id = %s", values)
            conn.commit()
        
        return SessionService.get_session_by_session_id(session_id)
    
    @staticmethod
    def update_last_activity(session_id: str) -> None:
        """Update session last activity timestamp."""
        last_activity = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_sessions SET last_activity = %s WHERE session_id = %s
            """, (last_activity, session_id))
            conn.commit()
    
    @staticmethod
    def switch_agent(session_id: str, agent_id: int) -> bool:
        """
        Switch active agent in a session.
        
        Args:
            session_id: Session ID string
            agent_id: Agent ID to switch to
            
        Returns:
            True if successful, False otherwise
        """
        session_update = SessionUpdate(active_agent_id=agent_id)
        result = SessionService.update_session(session_id, session_update)
        
        if result:
            logger.info(f"Session {session_id} switched to agent {agent_id}")
        
        return result is not None
    
    @staticmethod
    def update_active_corpora(session_id: str, corpus_ids: List[int]) -> bool:
        """
        Update active corpora in a session.
        
        Args:
            session_id: Session ID string
            corpus_ids: List of corpus IDs to set as active
            
        Returns:
            True if successful, False otherwise
        """
        session_update = SessionUpdate(active_corpora=corpus_ids)
        result = SessionService.update_session(session_id, session_update)
        
        if result:
            logger.info(f"Session {session_id} active corpora updated to {corpus_ids}")
        
        return result is not None
    
    @staticmethod
    def get_active_corpora(session_id: str) -> List[int]:
        """
        Get active corpora for a session.
        
        Args:
            session_id: Session ID string
            
        Returns:
            List of active corpus IDs
        """
        session = SessionService.get_session_by_session_id(session_id)
        return session.active_corpora if session and session.active_corpora else []
    
    @staticmethod
    def invalidate_session(session_id: str) -> bool:
        """
        Invalidate a session.
        
        Args:
            session_id: Session ID string
            
        Returns:
            True if successful, False otherwise
        """
        session_update = SessionUpdate(is_active=False)
        result = SessionService.update_session(session_id, session_update)
        
        if result:
            logger.info(f"Session {session_id} invalidated")
        
        return result is not None
    
    @staticmethod
    def cleanup_expired_sessions() -> int:
        """
        Clean up expired sessions.
        
        Marks sessions as inactive if:
          - expires_at has passed, OR
          - last_activity is older than SESSION_IDLE_HOURS (default 2h)
        
        Returns:
            Number of sessions cleaned up
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_sessions 
                SET is_active = FALSE 
                WHERE is_active = TRUE
                  AND (
                    expires_at < NOW()
                    OR last_activity < NOW() - INTERVAL '%s hours'
                  )
            """ % SESSION_IDLE_HOURS)
            conn.commit()
            count = cursor.rowcount
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired/idle sessions")
        
        return count
