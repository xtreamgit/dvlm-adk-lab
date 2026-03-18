"""
Corpus service for managing corpora and user access.
"""

import logging
import os
from typing import Optional, List, Dict

from database.repositories.corpus_repository import CorpusRepository
from models.corpus import Corpus, CorpusCreate, CorpusUpdate, CorpusWithAccess

logger = logging.getLogger(__name__)

# Import Vertex AI for document count retrieval
try:
    import vertexai
    from vertexai import rag
    import google.auth
    
    # Get project and location from config
    from config.config_loader import load_config
    account = os.getenv('ACCOUNT_ENV', 'develom')
    config = load_config(account)
    PROJECT_ID = config.PROJECT_ID
    LOCATION = config.LOCATION
    
    credentials, _ = google.auth.default()
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
    VERTEX_AI_AVAILABLE = True
except Exception as e:
    logger.warning(f"Vertex AI not available for document counts: {e}")
    VERTEX_AI_AVAILABLE = False


class CorpusService:
    """Service for corpus operations."""
    
    @staticmethod
    def _get_document_count(corpus_name: str, vertex_corpus_id: Optional[str] = None) -> int:
        """
        Get document count for a corpus from Vertex AI.
        
        Args:
            corpus_name: Display name of the corpus
            vertex_corpus_id: Optional Vertex AI corpus resource ID
            
        Returns:
            Number of documents in the corpus (0 if unavailable)
        """
        if not VERTEX_AI_AVAILABLE:
            return 0
            
        try:
            # If we have vertex_corpus_id, use it directly
            if vertex_corpus_id:
                files = rag.list_files(vertex_corpus_id)
                return len(list(files))
            
            # Otherwise, find corpus by display name
            corpora = rag.list_corpora()
            for corpus in corpora:
                if corpus.display_name == corpus_name:
                    files = rag.list_files(corpus.name)
                    return len(list(files))
            
            return 0
        except Exception as e:
            logger.debug(f"Could not fetch document count for corpus '{corpus_name}': {e}")
            return 0
    
    @staticmethod
    def create_corpus(corpus_create: CorpusCreate) -> Corpus:
        """
        Create a new corpus.
        
        Args:
            corpus_create: CorpusCreate model with corpus data
            
        Returns:
            Created Corpus object
            
        Raises:
            ValueError: If corpus name already exists
        """
        # Check if corpus name exists
        if CorpusRepository.get_by_name(corpus_create.name):
            raise ValueError(f"Corpus '{corpus_create.name}' already exists")
        
        corpus_dict = CorpusRepository.create(
            name=corpus_create.name,
            display_name=corpus_create.display_name,
            gcs_bucket=corpus_create.gcs_bucket,
            description=corpus_create.description,
            vertex_corpus_id=corpus_create.vertex_corpus_id
        )
        
        logger.info(f"Corpus created: {corpus_create.name} (ID: {corpus_dict['id']})")
        return Corpus(**corpus_dict)
    
    @staticmethod
    def get_corpus_by_id(corpus_id: int) -> Optional[Corpus]:
        """Get corpus by ID."""
        corpus_dict = CorpusRepository.get_by_id(corpus_id)
        return Corpus(**corpus_dict) if corpus_dict else None
    
    @staticmethod
    def get_corpus_by_name(name: str) -> Optional[Corpus]:
        """Get corpus by name."""
        corpus_dict = CorpusRepository.get_by_name(name)
        return Corpus(**corpus_dict) if corpus_dict else None
    
    @staticmethod
    def get_all_corpora(active_only: bool = True) -> List[Corpus]:
        """Get all corpora."""
        corpora_dict = CorpusRepository.get_all(active_only=active_only)
        return [Corpus(**c) for c in corpora_dict]
    
    @staticmethod
    def update_corpus(corpus_id: int, corpus_update: CorpusUpdate) -> Optional[Corpus]:
        """
        Update corpus information.
        
        Args:
            corpus_id: Corpus ID
            corpus_update: CorpusUpdate model with fields to update
            
        Returns:
            Updated Corpus object or None if not found
        """
        update_data = corpus_update.model_dump(exclude_unset=True)
        if not update_data:
            return CorpusService.get_corpus_by_id(corpus_id)
        
        corpus_dict = CorpusRepository.update(corpus_id, **update_data)
        return Corpus(**corpus_dict) if corpus_dict else None
    
    # ========== Group-Corpus Access ==========
    
    @staticmethod
    def grant_group_access(group_id: int, corpus_id: int, permission: str = 'read') -> bool:
        """
        Grant group access to a corpus.
        
        Args:
            group_id: Group ID
            corpus_id: Corpus ID
            permission: Permission level ('read', 'write', 'admin')
            
        Returns:
            True if successful, False otherwise
        """
        success = CorpusRepository.grant_group_access(group_id, corpus_id, permission)
        if success:
            logger.info(f"Group {group_id} granted {permission} access to corpus {corpus_id}")
        return success
    
    @staticmethod
    def revoke_group_access(group_id: int, corpus_id: int) -> bool:
        """
        Revoke group access to a corpus.
        
        Args:
            group_id: Group ID
            corpus_id: Corpus ID
            
        Returns:
            True if successful, False otherwise
        """
        success = CorpusRepository.revoke_group_access(group_id, corpus_id)
        if success:
            logger.info(f"Group {group_id} access revoked for corpus {corpus_id}")
        return success
    
    # ========== User-Corpus Access ==========
    
    @staticmethod
    def get_user_corpora(user_id: int, active_only: bool = True, 
                        active_in_session: Optional[List[int]] = None,
                        validate_with_vertex: bool = True) -> List[CorpusWithAccess]:
        """
        Get all corpora a user has access to.
        
        Args:
            user_id: User ID
            active_only: Only return active corpora
            active_in_session: List of corpus IDs that are active in the session
            validate_with_vertex: If True, only return corpora that exist in Vertex AI
            
        Returns:
            List of CorpusWithAccess objects
        """
        corpora_dict = CorpusRepository.get_user_corpora(user_id, active_only=active_only)
        
        # Validate against Vertex AI if requested
        if validate_with_vertex and VERTEX_AI_AVAILABLE:
            try:
                # Fetch corpus names from Vertex AI
                vertex_corpora = list(rag.list_corpora())
                # Use corpus.display_name from Vertex AI (which matches our 'name' field in DB)
                vertex_corpus_names = {corpus.display_name for corpus in vertex_corpora}
                
                # Filter out corpora that don't exist in Vertex AI
                before_count = len(corpora_dict)
                corpora_dict = [
                    c for c in corpora_dict 
                    if c['name'] in vertex_corpus_names  # Compare 'name' not 'display_name'
                ]
                filtered_count = before_count - len(corpora_dict)
                
                if filtered_count > 0:
                    logger.info(f"Filtered {filtered_count} corpus/corpora not found in Vertex AI")
            except Exception as e:
                logger.warning(f"Failed to validate corpora with Vertex AI: {e}")
                # Continue with unvalidated list if Vertex AI check fails
        
        active_set = set(active_in_session) if active_in_session else set()
        
        corpora = []
        for corpus_data in corpora_dict:
            # Fetch document count from Vertex AI
            doc_count = CorpusService._get_document_count(
                corpus_data.get('name', ''),
                corpus_data.get('vertex_corpus_id')
            )
            
            corpus = CorpusWithAccess(
                **{k: v for k, v in corpus_data.items() if k not in ('permission', 'document_count')},
                has_access=True,
                permission=corpus_data.get('permission'),
                is_active_in_session=(corpus_data['id'] in active_set),
                document_count=doc_count
            )
            corpora.append(corpus)
        
        return corpora
    
    @staticmethod
    def get_all_corpora_with_user_access(user_id: int, active_only: bool = True,
                                        validate_with_vertex: bool = True) -> List[CorpusWithAccess]:
        """
        Get all corpora with access information for a specific user.
        
        Returns all corpora (not just accessible ones) with has_access flag
        indicating whether the user can use each corpus.
        
        Args:
            user_id: User ID
            active_only: Only return active corpora
            validate_with_vertex: If True, only return corpora that exist in Vertex AI
            
        Returns:
            List of CorpusWithAccess objects with has_access flag for each
        """
        # Get all active corpora
        all_corpora_dict = CorpusRepository.get_all(active_only=active_only)
        
        # Validate against Vertex AI if requested
        if validate_with_vertex and VERTEX_AI_AVAILABLE:
            try:
                vertex_corpora = list(rag.list_corpora())
                # Use corpus.display_name from Vertex AI (which matches our 'name' field in DB)
                vertex_corpus_names = {corpus.display_name for corpus in vertex_corpora}
                
                before_count = len(all_corpora_dict)
                all_corpora_dict = [
                    c for c in all_corpora_dict 
                    if c['name'] in vertex_corpus_names  # Compare 'name' not 'display_name'
                ]
                filtered_count = before_count - len(all_corpora_dict)
                
                if filtered_count > 0:
                    logger.info(f"Filtered {filtered_count} corpus/corpora not found in Vertex AI")
            except Exception as e:
                logger.warning(f"Failed to validate corpora with Vertex AI: {e}")
        
        # Get user's accessible corpus IDs
        user_corpora = CorpusRepository.get_user_corpora(user_id, active_only=active_only)
        accessible_corpus_ids = {c['id'] for c in user_corpora}
        
        # Build result with access information
        corpora = []
        for corpus_data in all_corpora_dict:
            corpus_id = corpus_data['id']
            has_access = corpus_id in accessible_corpus_ids
            
            # Get permission if user has access
            permission = None
            if has_access:
                user_corpus = next((c for c in user_corpora if c['id'] == corpus_id), None)
                permission = user_corpus.get('permission') if user_corpus else None
            
            # document_count is already in corpus_data from the repository query
            # No need to fetch from Vertex AI
            
            corpus = CorpusWithAccess(
                **{k: v for k, v in corpus_data.items() if k != 'permission'},
                has_access=has_access,
                permission=permission,
                is_active_in_session=False
            )
            corpora.append(corpus)
        
        return corpora
    
    @staticmethod
    def validate_corpus_access(user_id: int, corpus_id: int) -> bool:
        """
        Check if user has access to a corpus.
        
        Args:
            user_id: User ID
            corpus_id: Corpus ID
            
        Returns:
            True if user has access, False otherwise
        """
        permission = CorpusRepository.check_user_access(user_id, corpus_id)
        return permission is not None
    
    @staticmethod
    def get_corpus_permission(user_id: int, corpus_id: int) -> Optional[str]:
        """
        Get user's permission level for a corpus.
        
        Args:
            user_id: User ID
            corpus_id: Corpus ID
            
        Returns:
            Permission string ('read', 'write', 'admin') or None if no access
        """
        return CorpusRepository.check_user_access(user_id, corpus_id)
    
    # ========== Session Corpus Management ==========
    
    @staticmethod
    def update_session_selection(user_id: int, corpus_id: int) -> bool:
        """
        Update session corpus selection for a user.
        
        Args:
            user_id: User ID
            corpus_id: Corpus ID
            
        Returns:
            True if successful
        """
        return CorpusRepository.update_session_selection(user_id, corpus_id)
    
    @staticmethod
    def restore_last_corpora(user_id: int, limit: int = 10) -> List[int]:
        """
        Get last selected corpus IDs for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of corpus IDs to return
            
        Returns:
            List of corpus IDs
        """
        return CorpusRepository.get_last_selected_corpora(user_id, limit=limit)
