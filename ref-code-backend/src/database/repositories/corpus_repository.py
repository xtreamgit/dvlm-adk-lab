"""
Corpus repository for database operations.
"""

import json
from typing import Optional, List, Dict
from datetime import datetime, timezone

from ..connection import get_db_connection


class CorpusRepository:
    """Repository for corpus-related database operations."""
    
    @staticmethod
    def get_by_id(corpus_id: int) -> Optional[Dict]:
        """Get corpus by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM corpora WHERE id = %s", (corpus_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_by_name(name: str) -> Optional[Dict]:
        """Get corpus by name."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM corpora WHERE name = %s", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def create(name: str, display_name: str, gcs_bucket: str,
              description: Optional[str] = None, vertex_corpus_id: Optional[str] = None) -> Dict:
        """Create a new corpus."""
        created_at = datetime.now(timezone.utc).isoformat()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO corpora (name, display_name, description, gcs_bucket, 
                                    vertex_corpus_id, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (name, display_name, description, gcs_bucket, vertex_corpus_id, True, created_at))
            result = cursor.fetchone()
            corpus_id = result['id'] if isinstance(result, dict) else result[0]
            conn.commit()
        
        return CorpusRepository.get_by_id(corpus_id)
    
    @staticmethod
    def get_all(active_only: bool = True) -> List[Dict]:
        """Get all corpora with document counts from metadata."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT c.*, COALESCE(cm.document_count, 0) as document_count
                FROM corpora c
                LEFT JOIN corpus_metadata cm ON c.id = cm.corpus_id
            """
            if active_only:
                query += " WHERE c.is_active = TRUE"
            query += " ORDER BY c.display_name"
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(corpus_id: int, **kwargs) -> Optional[Dict]:
        """Update corpus fields."""
        if not kwargs:
            return CorpusRepository.get_by_id(corpus_id)
        
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        values = list(kwargs.values()) + [corpus_id]
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE corpora SET {set_clause} WHERE id = %s", values)
            conn.commit()
        
        return CorpusRepository.get_by_id(corpus_id)
    
    # ========== Group-Corpus Access ==========
    
    @staticmethod
    def grant_group_access(group_id: int, corpus_id: int, permission: str = 'read') -> bool:
        """Grant group access to a corpus."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO group_corpus_access (group_id, corpus_id, permission)
                    VALUES (%s, %s, %s)
                """, (group_id, corpus_id, permission))
                conn.commit()
            return True
        except Exception:
            return False
    
    @staticmethod
    def revoke_group_access(group_id: int, corpus_id: int) -> bool:
        """Revoke group access to a corpus."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM group_corpus_access WHERE group_id = %s AND corpus_id = %s
            """, (group_id, corpus_id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def get_groups_for_corpus(corpus_id: int) -> List[Dict]:
        """Get all groups that have access to a corpus."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT gca.group_id, gca.permission, gca.granted_at
                FROM group_corpus_access gca
                WHERE gca.corpus_id = %s
            """, (corpus_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_user_corpora(user_id: int, active_only: bool = True) -> List[Dict]:
        """Get all corpora a user has access to (through their chatbot groups) with document counts."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT DISTINCT c.*, cca.permission, COALESCE(cm.document_count, 0) as document_count
                FROM corpora c
                JOIN chatbot_corpus_access cca ON c.id = cca.corpus_id
                JOIN chatbot_user_groups cug ON cca.chatbot_group_id = cug.chatbot_group_id
                JOIN chatbot_users cu ON cug.chatbot_user_id = cu.id
                LEFT JOIN corpus_metadata cm ON c.id = cm.corpus_id
                WHERE cu.user_id = %s
            """
            if active_only:
                query += " AND c.is_active = TRUE"
            query += " ORDER BY c.display_name"
            
            cursor.execute(query, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def check_user_access(user_id: int, corpus_id: int) -> Optional[str]:
        """
        Check if user has access to a corpus and return permission level.
        Returns permission string ('query', 'admin') or None.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cca.permission
                FROM chatbot_corpus_access cca
                JOIN chatbot_user_groups cug ON cca.chatbot_group_id = cug.chatbot_group_id
                JOIN chatbot_users cu ON cug.chatbot_user_id = cu.id
                WHERE cu.user_id = %s AND cca.corpus_id = %s
                ORDER BY 
                    CASE cca.permission 
                        WHEN 'admin' THEN 1 
                        WHEN 'query' THEN 2 
                    END
                LIMIT 1
            """, (user_id, corpus_id))
            row = cursor.fetchone()
            return row['permission'] if row else None
    
    # ========== Session Corpus Selections ==========
    
    @staticmethod
    def update_session_selection(user_id: int, corpus_id: int) -> bool:
        """Update or create session corpus selection."""
        last_selected_at = datetime.now(timezone.utc).isoformat()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO session_corpus_selections (user_id, corpus_id, last_selected_at)
                VALUES (%s, %s, %s)
                ON CONFLICT(user_id, corpus_id) 
                DO UPDATE SET last_selected_at = %s
            """, (user_id, corpus_id, last_selected_at, last_selected_at))
            conn.commit()
            return True
    
    @staticmethod
    def get_last_selected_corpora(user_id: int, limit: int = 10) -> List[int]:
        """Get last selected corpus IDs for a user."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT corpus_id FROM session_corpus_selections
                WHERE user_id = %s
                ORDER BY last_selected_at DESC
                LIMIT %s
            """, (user_id, limit))
            return [row['corpus_id'] for row in cursor.fetchall()]
