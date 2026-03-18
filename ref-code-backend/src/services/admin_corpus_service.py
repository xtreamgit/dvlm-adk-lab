"""
Admin corpus service for enhanced corpus management.
"""

import logging
from typing import List, Dict, Any, Optional
from database.repositories import (
    CorpusRepository,
    AuditRepository,
    CorpusMetadataRepository
)

logger = logging.getLogger(__name__)


class AdminCorpusService:
    """Service for admin corpus operations."""
    
    @staticmethod
    def get_all_with_details(include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all corpora with complete admin details.
        
        Args:
            include_inactive: Include inactive corpora
        
        Returns:
            List of corpus details with metadata, groups, and recent activity
        """
        corpora = CorpusRepository.get_all(active_only=not include_inactive)
        
        result = []
        for corpus in corpora:
            corpus_id = corpus['id']
            
            # Get metadata
            metadata = CorpusMetadataRepository.get_by_corpus_id(corpus_id)
            
            # Ensure metadata exists
            if not metadata:
                CorpusMetadataRepository.ensure_exists(corpus_id)
                metadata = CorpusMetadataRepository.get_by_corpus_id(corpus_id)
            
            # Get groups with access
            # Note: Legacy group access disabled - now using Google Groups Bridge
            groups_with_access = []
            # TODO: Implement Google Groups Bridge access listing
            
            # Get recent activity
            recent_activity = AuditRepository.get_recent_for_corpus(corpus_id, limit=5)
            
            result.append({
                **corpus,
                'metadata': metadata,
                'groups_with_access': groups_with_access,
                'recent_activity': recent_activity,
            })
        
        return result
    
    @staticmethod
    def get_corpus_detail(corpus_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a single corpus.
        
        Args:
            corpus_id: Corpus ID
        
        Returns:
            Corpus detail dictionary or None
        """
        corpus = CorpusRepository.get_by_id(corpus_id)
        if not corpus:
            return None
        
        # Get metadata
        metadata = CorpusMetadataRepository.get_by_corpus_id(corpus_id)
        if not metadata:
            CorpusMetadataRepository.ensure_exists(corpus_id)
            metadata = CorpusMetadataRepository.get_by_corpus_id(corpus_id)
        
        # Get groups with access
        # Note: Legacy group access disabled - now using Google Groups Bridge
        groups_with_access = []
        # TODO: Implement Google Groups Bridge access listing
        
        # Get recent activity
        recent_activity = AuditRepository.get_recent_for_corpus(corpus_id, limit=10)
        
        return {
            **corpus,
            'metadata': metadata,
            'groups_with_access': groups_with_access,
            'recent_activity': recent_activity,
        }
    
    @staticmethod
    def update_metadata(
        corpus_id: int,
        updates: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Update corpus metadata.
        
        Args:
            corpus_id: Corpus ID
            updates: Dictionary of fields to update
            user_id: User making the update
        
        Returns:
            Updated metadata
        """
        # Get before state
        before = CorpusMetadataRepository.get_by_corpus_id(corpus_id)
        
        # Update metadata
        rows_affected = CorpusMetadataRepository.update(corpus_id, updates)
        
        if rows_affected > 0:
            # Log the change
            after = CorpusMetadataRepository.get_by_corpus_id(corpus_id)
            AuditRepository.create({
                'corpus_id': corpus_id,
                'user_id': user_id,
                'action': 'updated',
                'changes': {
                    'before': before,
                    'after': after,
                    'fields': list(updates.keys())
                },
                'metadata': {'operation': 'update_metadata'}
            })
        
        return CorpusMetadataRepository.get_by_corpus_id(corpus_id)
    
    @staticmethod
    def update_corpus_status(
        corpus_id: int,
        is_active: bool,
        user_id: int
    ) -> bool:
        """
        Activate or deactivate a corpus.
        
        Args:
            corpus_id: Corpus ID
            is_active: New active status
            user_id: User making the change
        
        Returns:
            Success status
        """
        corpus = CorpusRepository.get_by_id(corpus_id)
        if not corpus:
            return False
        
        # Update status
        result = CorpusRepository.update(corpus_id, is_active=is_active)
        rows = 1 if result else 0
        
        if rows > 0:
            # Log the change
            action = 'activated' if is_active else 'deactivated'
            AuditRepository.create({
                'corpus_id': corpus_id,
                'user_id': user_id,
                'action': action,
                'changes': {
                    'before': {'is_active': corpus['is_active']},
                    'after': {'is_active': is_active}
                },
                'metadata': {'operation': 'update_status'}
            })
            
            return True
        
        return False
