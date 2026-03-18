"""
Corpus metadata repository for admin panel.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from database.connection import execute_query, execute_insert, execute_update

logger = logging.getLogger(__name__)


class CorpusMetadataRepository:
    """Repository for corpus metadata operations."""
    
    @staticmethod
    def create(corpus_id: int, created_by: Optional[int] = None, **kwargs) -> int:
        """
        Create metadata entry for a corpus.
        
        Args:
            corpus_id: Corpus ID
            created_by: User ID who created the corpus
            **kwargs: Additional metadata fields
        
        Returns:
            ID of created metadata entry
        """
        tags = kwargs.get('tags')
        if tags and isinstance(tags, (list, dict)):
            tags = json.dumps(tags)
        
        query = """
            INSERT INTO corpus_metadata 
            (corpus_id, created_by, created_at, sync_status, tags, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        return execute_insert(query, (
            corpus_id,
            created_by,
            datetime.utcnow().isoformat(),
            kwargs.get('sync_status', 'active'),
            tags,
            kwargs.get('notes')
        ))
    
    @staticmethod
    def get_by_corpus_id(corpus_id: int) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific corpus.
        
        Args:
            corpus_id: Corpus ID
        
        Returns:
            Metadata dictionary or None (with datetime objects converted to ISO strings)
        """
        query = """
            SELECT 
                cm.*,
                u1.email as created_by_name,
                u2.email as last_synced_by_name
            FROM corpus_metadata cm
            LEFT JOIN users u1 ON cm.created_by = u1.id
            LEFT JOIN users u2 ON cm.last_synced_by = u2.id
            WHERE cm.corpus_id = %s
        """
        
        results = execute_query(query, (corpus_id,))
        if not results:
            return None
        
        # Convert datetime objects to ISO strings for JSON serialization
        result = results[0]
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
        
        return result
    
    @staticmethod
    def update(corpus_id: int, updates: Dict[str, Any]) -> int:
        """
        Update corpus metadata.
        
        Args:
            corpus_id: Corpus ID
            updates: Dictionary of fields to update
        
        Returns:
            Number of affected rows
        """
        set_clauses = []
        params = []
        
        if 'tags' in updates:
            tags = updates['tags']
            if isinstance(tags, (list, dict)):
                tags = json.dumps(tags)
            set_clauses.append("tags = %s")
            params.append(tags)
        
        if 'notes' in updates:
            set_clauses.append("notes = %s")
            params.append(updates['notes'])
        
        if 'sync_status' in updates:
            set_clauses.append("sync_status = %s")
            params.append(updates['sync_status'])
        
        if 'sync_error_message' in updates:
            set_clauses.append("sync_error_message = %s")
            params.append(updates['sync_error_message'])
        
        if 'document_count' in updates:
            set_clauses.append("document_count = %s")
            params.append(updates['document_count'])
            set_clauses.append("last_document_count_update = %s")
            params.append(datetime.utcnow().isoformat())
        
        if 'last_synced_by' in updates:
            set_clauses.append("last_synced_by = %s")
            params.append(updates['last_synced_by'])
            set_clauses.append("last_synced_at = %s")
            params.append(datetime.utcnow().isoformat())
        
        if not set_clauses:
            return 0
        
        query = f"""
            UPDATE corpus_metadata
            SET {', '.join(set_clauses)}
            WHERE corpus_id = %s
        """
        params.append(corpus_id)
        
        return execute_update(query, tuple(params))
    
    @staticmethod
    def update_sync_status(
        corpus_id: int,
        status: str,
        user_id: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> int:
        """
        Update sync status for a corpus.
        
        Args:
            corpus_id: Corpus ID
            status: New sync status
            user_id: User who triggered the sync
            error_message: Error message if sync failed
        
        Returns:
            Number of affected rows
        """
        query = """
            UPDATE corpus_metadata
            SET sync_status = %s,
                sync_error_message = %s,
                last_synced_at = %s,
                last_synced_by = %s
            WHERE corpus_id = %s
        """
        
        return execute_update(query, (
            status,
            error_message,
            datetime.utcnow().isoformat(),
            user_id,
            corpus_id
        ))
    
    @staticmethod
    def update_document_count(corpus_id: int, count: int) -> int:
        """
        Update document count for a corpus.
        
        Args:
            corpus_id: Corpus ID
            count: New document count
        
        Returns:
            Number of affected rows
        """
        query = """
            UPDATE corpus_metadata
            SET document_count = %s,
                last_document_count_update = %s
            WHERE corpus_id = %s
        """
        
        return execute_update(query, (
            count,
            datetime.utcnow().isoformat(),
            corpus_id
        ))
    
    @staticmethod
    def get_all_with_status(status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all corpus metadata, optionally filtered by status.
        
        Args:
            status: Optional status filter
        
        Returns:
            List of metadata entries (with datetime objects converted to ISO strings)
        """
        if status:
            query = """
                SELECT 
                    cm.*,
                    c.name as corpus_name,
                    c.display_name as corpus_display_name,
                    u1.email as created_by_name,
                    u2.email as last_synced_by_name
                FROM corpus_metadata cm
                LEFT JOIN corpora c ON cm.corpus_id = c.id
                LEFT JOIN users u1 ON cm.created_by = u1.id
                LEFT JOIN users u2 ON cm.last_synced_by = u2.id
                WHERE cm.sync_status = %s
                ORDER BY cm.last_synced_at DESC
            """
            results = execute_query(query, (status,))
        else:
            query = """
                SELECT 
                    cm.*,
                    c.name as corpus_name,
                    c.display_name as corpus_display_name,
                    u1.email as created_by_name,
                    u2.email as last_synced_by_name
                FROM corpus_metadata cm
                LEFT JOIN corpora c ON cm.corpus_id = c.id
                LEFT JOIN users u1 ON cm.created_by = u1.id
                LEFT JOIN users u2 ON cm.last_synced_by = u2.id
                ORDER BY cm.last_synced_at DESC
            """
            results = execute_query(query)
        
        # Convert datetime objects to ISO strings for JSON serialization
        for result in results:
            for key, value in result.items():
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
        
        return results
    
    @staticmethod
    def ensure_exists(corpus_id: int, created_by: Optional[int] = None) -> None:
        """
        Ensure metadata entry exists for a corpus, create if missing.
        
        Args:
            corpus_id: Corpus ID
            created_by: User ID who created the corpus
        """
        existing = CorpusMetadataRepository.get_by_corpus_id(corpus_id)
        if not existing:
            CorpusMetadataRepository.create(corpus_id, created_by)
