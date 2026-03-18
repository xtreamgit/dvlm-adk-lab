"""
Bulk operation service for admin panel.
"""

import logging
from typing import List, Dict, Any
from database.repositories import CorpusRepository, AuditRepository

logger = logging.getLogger(__name__)


class BulkOperationService:
    """Service for bulk corpus operations."""
    
    @staticmethod
    def grant_access(
        corpus_ids: List[int],
        group_id: int,
        permission: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Grant group access to multiple corpora.
        
        Args:
            corpus_ids: List of corpus IDs
            group_id: Group ID to grant access to
            permission: Permission level
            user_id: User performing the operation
        
        Returns:
            Result summary
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        for corpus_id in corpus_ids:
            try:
                # Check if corpus exists
                corpus = CorpusRepository.get_by_id(corpus_id)
                if not corpus:
                    errors.append({
                        'corpus_id': corpus_id,
                        'error': 'Corpus not found'
                    })
                    failed_count += 1
                    continue
                
                # Grant access
                GroupCorpusAccessRepository.grant_access(
                    group_id=group_id,
                    corpus_id=corpus_id,
                    permission=permission
                )
                
                # Log the action
                AuditRepository.create({
                    'corpus_id': corpus_id,
                    'user_id': user_id,
                    'action': 'granted_access',
                    'changes': {
                        'group_id': group_id,
                        'permission': permission
                    },
                    'metadata': {'operation': 'bulk_grant'}
                })
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to grant access for corpus {corpus_id}: {e}")
                errors.append({
                    'corpus_id': corpus_id,
                    'error': str(e)
                })
                failed_count += 1
        
        return {
            'success': failed_count == 0,
            'processed_count': success_count,
            'failed_count': failed_count,
            'errors': errors
        }
    
    @staticmethod
    def revoke_access(
        corpus_ids: List[int],
        group_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Revoke group access from multiple corpora.
        
        Args:
            corpus_ids: List of corpus IDs
            group_id: Group ID to revoke access from
            user_id: User performing the operation
        
        Returns:
            Result summary
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        for corpus_id in corpus_ids:
            try:
                # Revoke access
                GroupCorpusAccessRepository.revoke_access(
                    group_id=group_id,
                    corpus_id=corpus_id
                )
                
                # Log the action
                AuditRepository.create({
                    'corpus_id': corpus_id,
                    'user_id': user_id,
                    'action': 'revoked_access',
                    'changes': {
                        'group_id': group_id
                    },
                    'metadata': {'operation': 'bulk_revoke'}
                })
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to revoke access for corpus {corpus_id}: {e}")
                errors.append({
                    'corpus_id': corpus_id,
                    'error': str(e)
                })
                failed_count += 1
        
        return {
            'success': failed_count == 0,
            'processed_count': success_count,
            'failed_count': failed_count,
            'errors': errors
        }
    
    @staticmethod
    def update_status(
        corpus_ids: List[int],
        is_active: bool,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Update active status for multiple corpora.
        
        Args:
            corpus_ids: List of corpus IDs
            is_active: New active status
            user_id: User performing the operation
        
        Returns:
            Result summary
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        for corpus_id in corpus_ids:
            try:
                # Update status
                result = CorpusRepository.update(corpus_id, is_active=is_active)
                rows = 1 if result else 0
                
                if rows > 0:
                    # Log the action
                    action = 'activated' if is_active else 'deactivated'
                    AuditRepository.create({
                        'corpus_id': corpus_id,
                        'user_id': user_id,
                        'action': action,
                        'changes': {
                            'is_active': is_active
                        },
                        'metadata': {'operation': 'bulk_status_update'}
                    })
                    
                    success_count += 1
                else:
                    errors.append({
                        'corpus_id': corpus_id,
                        'error': 'No changes made'
                    })
                    failed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to update status for corpus {corpus_id}: {e}")
                errors.append({
                    'corpus_id': corpus_id,
                    'error': str(e)
                })
                failed_count += 1
        
        return {
            'success': failed_count == 0,
            'processed_count': success_count,
            'failed_count': failed_count,
            'errors': errors
        }
