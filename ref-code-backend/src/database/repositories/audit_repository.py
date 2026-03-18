"""
Audit log repository for tracking corpus changes.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from database.connection import execute_query, execute_insert

logger = logging.getLogger(__name__)


class AuditRepository:
    """Repository for corpus audit log operations."""
    
    @staticmethod
    def create(audit_data: Dict[str, Any]) -> int:
        """
        Create a new audit log entry.
        
        Args:
            audit_data: Dictionary containing:
                - corpus_id (optional)
                - user_id (optional)
                - action (required)
                - changes (optional, dict will be JSON serialized)
                - metadata (optional, dict will be JSON serialized)
        
        Returns:
            ID of created audit log entry
        """
        changes = audit_data.get('changes')
        if changes and isinstance(changes, dict):
            changes = json.dumps(changes)
        
        metadata = audit_data.get('metadata')
        if metadata and isinstance(metadata, dict):
            metadata = json.dumps(metadata)
        
        query = """
            INSERT INTO corpus_audit_log 
            (corpus_id, user_id, action, changes, metadata, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        return execute_insert(query, (
            audit_data.get('corpus_id'),
            audit_data.get('user_id'),
            audit_data['action'],
            changes,
            metadata,
            datetime.utcnow().isoformat()
        ))
    
    @staticmethod
    def get_by_corpus_id(corpus_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit log entries for a specific corpus.
        
        Args:
            corpus_id: Corpus ID
            limit: Maximum number of entries to return
        
        Returns:
            List of audit log entries with user and corpus names
        """
        query = """
            SELECT 
                cal.*,
                c.name as corpus_name,
                c.display_name as corpus_display_name,
                u.email as user_name
            FROM corpus_audit_log cal
            LEFT JOIN corpora c ON cal.corpus_id = c.id
            LEFT JOIN users u ON cal.user_id = u.id
            WHERE cal.corpus_id = %s
            ORDER BY cal.timestamp DESC
            LIMIT %s
        """
        
        return execute_query(query, (corpus_id, limit))
    
    @staticmethod
    def get_by_user_id(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit log entries for a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum number of entries to return
        
        Returns:
            List of audit log entries
        """
        query = """
            SELECT 
                cal.*,
                c.name as corpus_name,
                c.display_name as corpus_display_name,
                u.email as user_name
            FROM corpus_audit_log cal
            LEFT JOIN corpora c ON cal.corpus_id = c.id
            LEFT JOIN users u ON cal.user_id = u.id
            WHERE cal.user_id = %s
            ORDER BY cal.timestamp DESC
            LIMIT %s
        """
        
        return execute_query(query, (user_id, limit))
    
    @staticmethod
    def get_all(
        corpus_id: Optional[int] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries with optional filters.
        
        Args:
            corpus_id: Filter by corpus ID
            user_id: Filter by user ID
            action: Filter by action type
            limit: Maximum number of entries
            offset: Pagination offset
        
        Returns:
            List of audit log entries
        """
        conditions = []
        params = []
        
        if corpus_id is not None:
            conditions.append("cal.corpus_id = %s")
            params.append(corpus_id)
        
        if user_id is not None:
            conditions.append("cal.user_id = %s")
            params.append(user_id)
        
        if action:
            conditions.append("cal.action = %s")
            params.append(action)
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        query = f"""
            SELECT 
                cal.*,
                c.name as corpus_name,
                c.display_name as corpus_display_name,
                u.email as user_name
            FROM corpus_audit_log cal
            LEFT JOIN corpora c ON cal.corpus_id = c.id
            LEFT JOIN users u ON cal.user_id = u.id
            {where_clause}
            ORDER BY cal.timestamp DESC
            LIMIT %s OFFSET %s
        """
        
        params.extend([limit, offset])
        return execute_query(query, tuple(params))
    
    @staticmethod
    def get_recent_for_corpus(corpus_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent audit entries for a corpus (for dashboard display).
        
        Args:
            corpus_id: Corpus ID
            limit: Number of recent entries
        
        Returns:
            List of recent audit log entries
        """
        return AuditRepository.get_by_corpus_id(corpus_id, limit)
    
    @staticmethod
    def get_action_counts(corpus_id: Optional[int] = None) -> Dict[str, int]:
        """
        Get count of each action type.
        
        Args:
            corpus_id: Optional corpus ID to filter by
        
        Returns:
            Dictionary of action -> count
        """
        where_clause = ""
        params = ()
        
        if corpus_id is not None:
            where_clause = "WHERE corpus_id = %s"
            params = (corpus_id,)
        
        query = f"""
            SELECT action, COUNT(*) as count
            FROM corpus_audit_log
            {where_clause}
            GROUP BY action
            ORDER BY count DESC
        """
        
        results = execute_query(query, params)
        return {row['action']: row['count'] for row in results}
