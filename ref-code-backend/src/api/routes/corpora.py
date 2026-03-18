"""
Corpus management routes: list corpora, manage access, session corpus selection.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from services.corpus_service import CorpusService
from services.session_service import SessionService
from models.corpus import Corpus, CorpusCreate, CorpusUpdate, CorpusWithAccess
from models.user import User
from middleware.iap_auth_middleware import get_current_user_iap as get_current_user
from database.repositories import AuditRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/corpora", tags=["Corpora"])


class CorpusAccessRequest(BaseModel):
    """Request to grant corpus access."""
    group_id: int
    permission: str = "read"  # read, write, admin


class ActiveCorporaRequest(BaseModel):
    """Request to update active corpora."""
    corpus_ids: List[int]


# ========== Corpus CRUD ==========

@router.get("/", response_model=List[CorpusWithAccess])
async def list_my_corpora(current_user: User = Depends(get_current_user)):
    """
    Get all corpora current user has access to.
    
    Returns corpora with access information and active status.
    """
    return CorpusService.get_user_corpora(current_user.id, active_only=True)


@router.get("/all-with-access", response_model=List[CorpusWithAccess])
async def list_all_corpora_with_access(current_user: User = Depends(get_current_user)):
    """
    Get all active corpora with access information for current user.
    
    Returns all corpora regardless of access, with has_access flag indicating
    whether the current user can use each corpus.
    """
    return CorpusService.get_all_corpora_with_user_access(current_user.id, active_only=True)


@router.get("/all", response_model=List[Corpus])
async def list_all_corpora(
    current_user: User = Depends(get_current_user)  # TODO: Add Google Groups admin check
):
    """
    List all corpora in the system (admin only).
    
    Requires 'manage:corpora' permission.
    """
    return CorpusService.get_all_corpora(active_only=False)


@router.get("/{corpus_id}", response_model=Corpus)
async def get_corpus(
    corpus_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get corpus details by ID.
    
    User must have access to the corpus.
    """
    # Check user has access
    if not CorpusService.validate_corpus_access(current_user.id, corpus_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this corpus"
        )
    
    corpus = CorpusService.get_corpus_by_id(corpus_id)
    
    if not corpus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found"
        )
    
    return corpus


@router.post("/", response_model=Corpus, status_code=status.HTTP_201_CREATED)
async def create_corpus(
    corpus_create: CorpusCreate,
    current_user: User = Depends(get_current_user)  # TODO: Add Google Groups admin check
):
    """
    Create a new corpus (admin only).
    
    Requires 'create:corpus' permission.
    """
    try:
        corpus = CorpusService.create_corpus(corpus_create)
        logger.info(f"Corpus created by {current_user.email}: {corpus.name}")
        
        # Create audit log entry
        AuditRepository.create({
            'corpus_id': corpus.id,
            'user_id': current_user.id,
            'action': 'created',
            'changes': {
                'name': corpus.name,
                'display_name': corpus.display_name,
                'gcs_bucket': corpus.gcs_bucket
            },
            'metadata': {'source': 'user_api', 'user_email': current_user.email}
        })
        
        return corpus
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{corpus_id}", response_model=Corpus)
async def update_corpus(
    corpus_id: int,
    corpus_update: CorpusUpdate,
    current_user: User = Depends(get_current_user)  # TODO: Add Google Groups admin check
):
    """
    Update corpus (admin only).
    
    Requires 'update:corpus' permission.
    """
    updated_corpus = CorpusService.update_corpus(corpus_id, corpus_update)
    
    if not updated_corpus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found"
        )
    
    logger.info(f"Corpus updated by {current_user.email}: {updated_corpus.name}")
    
    # Create audit log entry
    AuditRepository.create({
        'corpus_id': corpus_id,
        'user_id': current_user.id,
        'action': 'updated',
        'changes': corpus_update.dict(exclude_unset=True),
        'metadata': {'source': 'user_api', 'email': current_user.email}
    })
    
    return updated_corpus


# ========== Corpus Access Management ==========

@router.post("/{corpus_id}/grant")
async def grant_corpus_access(
    corpus_id: int,
    access_request: CorpusAccessRequest,
    current_user: User = Depends(get_current_user)  # TODO: Add Google Groups admin check
):
    """
    Grant group access to a corpus (admin only).
    
    Requires 'manage:corpus_access' permission.
    
    - **group_id**: Group to grant access to
    - **permission**: Permission level ('read', 'write', 'admin')
    """
    # Verify corpus exists
    corpus = CorpusService.get_corpus_by_id(corpus_id)
    if not corpus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found"
        )
    
    # Note: Legacy group access endpoint - deprecated
    # Group access is now managed via Google Groups Bridge
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Legacy group access endpoint deprecated. Use Google Groups Bridge instead."
    )
    
    # Validate permission level
    if access_request.permission not in ["read", "write", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid permission level. Must be 'read', 'write', or 'admin'"
        )
    
    success = CorpusService.grant_group_access(
        access_request.group_id,
        corpus_id,
        access_request.permission
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to grant access (may already have access)"
        )
    
    logger.info(
        f"Group {group.name} granted {access_request.permission} access "
        f"to corpus {corpus.name} by {current_user.email}"
    )
    
    # Create audit log entry
    AuditRepository.create({
        'corpus_id': corpus_id,
        'user_id': current_user.id,
        'action': 'granted_access',
        'changes': {
            'group_id': access_request.group_id,
            'group_name': group.name,
            'permission': access_request.permission
        },
        'metadata': {'source': 'user_api', 'email': current_user.email}
    })
    
    return {"message": "Access granted successfully"}


@router.delete("/{corpus_id}/revoke/{group_id}")
async def revoke_corpus_access(
    corpus_id: int,
    group_id: int,
    current_user: User = Depends(get_current_user)  # TODO: Add Google Groups admin check
):
    """
    Revoke group access to a corpus (admin only).
    
    Requires 'manage:corpus_access' permission.
    """
    success = CorpusService.revoke_group_access(group_id, corpus_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access not found or already revoked"
        )
    
    logger.info(f"Group {group_id} access revoked for corpus {corpus_id} by {current_user.email}")
    
    # Create audit log entry
    AuditRepository.create({
        'corpus_id': corpus_id,
        'user_id': current_user.id,
        'action': 'revoked_access',
        'changes': {'group_id': group_id},
        'metadata': {'source': 'user_api', 'email': current_user.email}
    })
    
    return {"message": "Access revoked successfully"}


# ========== Session Corpus Management ==========

@router.get("/sessions/{session_id}/active", response_model=List[int])
async def get_active_corpora(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get active corpora for a session.
    
    Returns list of corpus IDs that are active in the session.
    """
    # Verify session exists and belongs to user
    session = SessionService.get_session_by_session_id(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session does not belong to you"
        )
    
    return SessionService.get_active_corpora(session_id)


@router.put("/sessions/{session_id}/active")
async def update_active_corpora(
    session_id: str,
    active_corpora: ActiveCorporaRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update active corpora for a session.
    
    - **corpus_ids**: List of corpus IDs to set as active
    
    User must have access to all specified corpora.
    """
    # Verify session exists and belongs to user
    session = SessionService.get_session_by_session_id(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session does not belong to you"
        )
    
    # Verify user has access to all corpora
    for corpus_id in active_corpora.corpus_ids:
        if not CorpusService.validate_corpus_access(current_user.id, corpus_id):
            corpus = CorpusService.get_corpus_by_id(corpus_id)
            corpus_name = corpus.name if corpus else f"ID:{corpus_id}"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have access to corpus: {corpus_name}"
            )
    
    # Update active corpora
    success = SessionService.update_active_corpora(session_id, active_corpora.corpus_ids)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update active corpora"
        )
    
    # Update session corpus selections for restoration
    for corpus_id in active_corpora.corpus_ids:
        CorpusService.update_session_selection(current_user.id, corpus_id)
    
    logger.info(
        f"User {current_user.email} updated session {session_id} "
        f"active corpora to {active_corpora.corpus_ids}"
    )
    
    return {
        "message": "Active corpora updated successfully",
        "session_id": session_id,
        "active_corpora": active_corpora.corpus_ids
    }


@router.get("/restore-last")
async def restore_last_corpora(
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    """
    Get last selected corpus IDs for restoration.
    
    Returns list of corpus IDs from last session.
    """
    corpus_ids = CorpusService.restore_last_corpora(current_user.id, limit=limit)
    
    return {
        "corpus_ids": corpus_ids,
        "count": len(corpus_ids)
    }
