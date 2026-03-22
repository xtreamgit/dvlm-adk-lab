"""
Admin API routes for corpus management.
Requires admin permissions.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
import os

from middleware.iap_auth_middleware import get_current_user_iap as get_current_user_hybrid
from models.user import User
from models.admin import (
    AdminCorpusDetail,
    AuditLogEntry,
    CorpusMetadataUpdate,
    BulkGrantRequest,
    BulkStatusUpdate,
    BulkOperationResult,
    PermissionGrantRequest,
    SyncResult,
    AdminUserDetail,
    AdminUserCreate,
    AdminUserUpdate,
    UserGroupAssignment,
)
from services.admin_corpus_service import AdminCorpusService
from services.bulk_operation_service import BulkOperationService
from database.repositories import AuditRepository, CorpusMetadataRepository, CorpusRepository, UserRepository
from database.connection import get_db_connection

logger = logging.getLogger(__name__)


def _get_chatbot_group_by_id(group_id: int) -> Optional[dict]:
    """Look up a chatbot group by ID. Replaces legacy GroupRepository.get_group_by_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, is_active FROM chatbot_groups WHERE id = %s",
            (group_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

router = APIRouter(prefix="/api/admin", tags=["Admin"])


async def require_admin(current_user: User = Depends(get_current_user_hybrid)) -> User:
    """Dependency to require admin privileges via Google Groups Bridge.
    
    Note: Admin access is now managed via Google Groups (admin-users group).
    This check is deprecated and will be replaced with Google Groups Bridge validation.
    For now, we allow all authenticated users (IAP handles authentication).
    """
    # TODO: Implement Google Groups Bridge admin check
    # Check if user is in 'admin-users' Google Group via chatbot_groups
    logger.warning("Admin check using legacy group system - needs Google Groups Bridge integration")
    
    # For now, allow all authenticated IAP users
    # In production, this should check Google Groups membership
    return current_user


# ========== Corpus Management ==========

@router.get("/corpora", response_model=List[AdminCorpusDetail])
async def list_all_corpora_admin(
    include_inactive: bool = Query(False, description="Include inactive corpora"),
    current_user: User = Depends(require_admin)
):
    """
    Get all corpora with full admin details.
    Includes metadata, groups with access, and recent activity.
    """
    try:
        corpora = AdminCorpusService.get_all_with_details(include_inactive)
        return corpora
    except Exception as e:
        logger.error(f"Failed to get admin corpora: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corpora/{corpus_id}", response_model=AdminCorpusDetail)
async def get_corpus_detail(
    corpus_id: int,
    current_user: User = Depends(require_admin)
):
    """Get detailed information for a single corpus."""
    try:
        corpus = AdminCorpusService.get_corpus_detail(corpus_id)
        if not corpus:
            raise HTTPException(status_code=404, detail="Corpus not found")
        return corpus
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get corpus detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corpora/{corpus_id}/audit", response_model=List[AuditLogEntry])
async def get_corpus_audit_log(
    corpus_id: int,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin)
):
    """Get audit history for a specific corpus."""
    try:
        logs = AuditRepository.get_by_corpus_id(corpus_id, limit)
        return logs
    except Exception as e:
        logger.error(f"Failed to get audit log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/corpora/{corpus_id}/metadata")
async def update_corpus_metadata(
    corpus_id: int,
    metadata: CorpusMetadataUpdate,
    current_user: User = Depends(require_admin)
):
    """Update corpus metadata (tags, notes, sync status)."""
    try:
        updates = metadata.dict(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        result = AdminCorpusService.update_metadata(
            corpus_id,
            updates,
            current_user.id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/corpora/{corpus_id}/status")
async def update_corpus_status(
    corpus_id: int,
    is_active: bool,
    current_user: User = Depends(require_admin)
):
    """Activate or deactivate a corpus."""
    try:
        success = AdminCorpusService.update_corpus_status(
            corpus_id,
            is_active,
            current_user.id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Corpus not found")
        
        return {
            "success": True,
            "corpus_id": corpus_id,
            "is_active": is_active
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update corpus status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/corpora/{corpus_id}/permissions/grant")
async def grant_corpus_permission(
    corpus_id: int,
    grant: PermissionGrantRequest,
    current_user: User = Depends(require_admin)
):
    """Grant group access to a corpus."""
    try:
        CorpusRepository.grant_group_access(
            group_id=grant.group_id,
            corpus_id=corpus_id,
            permission=grant.permission
        )
        
        # Log the action
        AuditRepository.create({
            'corpus_id': corpus_id,
            'user_id': current_user.id,
            'action': 'granted_access',
            'changes': {
                'group_id': grant.group_id,
                'permission': grant.permission
            },
            'metadata': {'operation': 'grant_permission'}
        })
        
        return {
            "success": True,
            "corpus_id": corpus_id,
            "group_id": grant.group_id,
            "permission": grant.permission
        }
    except Exception as e:
        logger.error(f"Failed to grant permission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/corpora/{corpus_id}/permissions/{group_id}")
async def revoke_corpus_permission(
    corpus_id: int,
    group_id: int,
    current_user: User = Depends(require_admin)
):
    """Revoke group access from a corpus."""
    try:
        CorpusRepository.revoke_group_access(
            group_id=group_id,
            corpus_id=corpus_id
        )
        
        # Log the action
        AuditRepository.create({
            'corpus_id': corpus_id,
            'user_id': current_user.id,
            'action': 'revoked_access',
            'changes': {
                'group_id': group_id
            },
            'metadata': {'operation': 'revoke_permission'}
        })
        
        return {
            "success": True,
            "corpus_id": corpus_id,
            "group_id": group_id
        }
    except Exception as e:
        logger.error(f"Failed to revoke permission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Bulk Operations ==========

@router.post("/corpora/bulk/grant-access", response_model=BulkOperationResult)
async def bulk_grant_access(
    request: BulkGrantRequest,
    current_user: User = Depends(require_admin)
):
    """Grant access to multiple corpora at once."""
    try:
        result = BulkOperationService.grant_access(
            corpus_ids=request.corpus_ids,
            group_id=request.group_id,
            permission=request.permission,
            user_id=current_user.id
        )
        return result
    except Exception as e:
        logger.error(f"Failed to bulk grant access: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/corpora/bulk/update-status", response_model=BulkOperationResult)
async def bulk_update_status(
    request: BulkStatusUpdate,
    current_user: User = Depends(require_admin)
):
    """Activate or deactivate multiple corpora."""
    try:
        result = BulkOperationService.update_status(
            corpus_ids=request.corpus_ids,
            is_active=request.is_active,
            user_id=current_user.id
        )
        return result
    except Exception as e:
        logger.error(f"Failed to bulk update status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Audit Log ==========

@router.get("/audit", response_model=List[AuditLogEntry])
async def get_audit_log(
    corpus_id: Optional[int] = Query(None, description="Filter by corpus ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin)
):
    """Get audit log with optional filters."""
    try:
        logs = AuditRepository.get_all(
            corpus_id=corpus_id,
            user_id=user_id,
            action=action,
            limit=limit,
            offset=offset
        )
        return logs
    except Exception as e:
        logger.error(f"Failed to get audit log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/actions")
async def get_action_counts(
    corpus_id: Optional[int] = Query(None, description="Filter by corpus ID"),
    current_user: User = Depends(require_admin)
):
    """Get count of each action type in audit log."""
    try:
        counts = AuditRepository.get_action_counts(corpus_id)
        return counts
    except Exception as e:
        logger.error(f"Failed to get action counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Sync Operations ==========

@router.post("/corpora/sync", response_model=SyncResult)
async def trigger_corpus_sync(
    current_user: User = Depends(require_admin)
):
    """
    Trigger manual sync with Vertex AI.
    This will add new corpora from Vertex AI and deactivate ones that no longer exist.
    """
    try:
        from services.corpus_sync_service import CorpusSyncService
        from config.config_loader import load_config
        import os
        
        # Get project and location from config
        account = os.getenv('ACCOUNT_ENV', 'develom')
        config = load_config(account)
        project_id = config.PROJECT_ID
        location = config.LOCATION
        
        # Run sync using the service
        result = CorpusSyncService.sync_from_vertex(project_id, location)
        
        # Log audit entries for added corpora
        if result['added'] > 0:
            try:
                from database.repositories import CorpusRepository
                # Get recently added corpora (those added in this sync)
                all_corpora = CorpusRepository.get_all(active_only=True)
                for corpus in all_corpora[-result['added']:]:  # Last N added
                    AuditRepository.create({
                        'corpus_id': corpus['id'],
                        'user_id': current_user.id,
                        'action': 'created',
                        'changes': {'source': 'vertex_ai_sync'},
                        'metadata': {'operation': 'manual_sync'}
                    })
            except Exception as e:
                logger.warning(f"Failed to create audit entries: {e}")
        
        # Convert to SyncResult model
        return SyncResult(
            success=result['status'] in ['success', 'partial'],
            total_corpora=result['vertex_count'],
            added_count=result['added'],
            deactivated_count=result['deactivated'],
            updated_count=result['updated'],
            errors=result['errors'],
            message=f"Sync complete: {result['added']} added, {result['updated']} updated, {result['deactivated']} deactivated"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync corpora: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/corpora/bootstrap-vertex")
async def bootstrap_vertex_corpus(
    current_user: User = Depends(require_admin),
):
    try:
        from config.config_loader import load_config
        import google.auth
        import vertexai
        from vertexai import rag

        account = os.getenv("ACCOUNT_ENV", "develom")
        config = load_config(account)
        project_id = config.PROJECT_ID
        location = config.LOCATION

        corpus_display_name = "adk-rag-default-corpus-dvlm-adk-lab"
        gcs_prefix = "gs://adk-rag-default-corpus-bucket-dvlm-adk-lab/documents"
        embedding_model = "publishers/google/models/text-embedding-005"

        credentials, adc_project = google.auth.default()
        vertexai.init(project=project_id, location=location, credentials=credentials)

        existing = None
        for c in rag.list_corpora():
            if getattr(c, "display_name", None) == corpus_display_name:
                existing = c
                break

        created = False
        corpus = existing
        if corpus is None:
            embedding_model_config = rag.RagEmbeddingModelConfig(
                vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                    publisher_model=embedding_model,
                ),
            )

            corpus = rag.create_corpus(
                display_name=corpus_display_name,
                backend_config=rag.RagVectorDbConfig(
                    rag_embedding_model_config=embedding_model_config,
                ),
            )
            created = True

        transformation_config = rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(
                chunk_size=512,
                chunk_overlap=100,
            ),
        )

        import_result = rag.import_files(
            corpus.name,
            [gcs_prefix],
            transformation_config=transformation_config,
            max_embedding_requests_per_min=1000,
        )

        return {
            "status": "success",
            "effective_project_id": project_id,
            "effective_location": location,
            "adc_project": adc_project,
            "corpus_display_name": corpus.display_name,
            "corpus_resource_name": corpus.name,
            "corpus_created": created,
            "gcs_prefix": gcs_prefix,
            "imported_rag_files_count": getattr(import_result, "imported_rag_files_count", None),
        }
    except Exception as e:
        logger.error(f"Failed to bootstrap Vertex corpus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== User Management Endpoints ==========

@router.get("/users", response_model=List[AdminUserDetail])
async def list_all_users(
    current_user: User = Depends(require_admin)
):
    """Get all users with their group memberships."""
    try:
        from services.user_service import UserService
        
        users = UserService.get_all_users()
        user_details = []
        
        for user in users:
            # Get user's groups
            group_ids = UserService.get_user_groups(user.id)
            groups = []
            for gid in group_ids:
                group = _get_chatbot_group_by_id(gid)
                if group:
                    groups.append({
                        'id': group['id'],
                        'name': group['name'],
                        'description': group.get('description', '')
                    })
            
            user_details.append(AdminUserDetail(
                id=user.id,
                username=user.email.split('@')[0],
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                groups=groups
            ))
        
        return user_details
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.post("/users", response_model=AdminUserDetail, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: AdminUserCreate,
    current_user: User = Depends(require_admin)
):
    """Create a new user (admin only)."""
    logger.info(f"Creating user with data: email={user_create.email}, groups={user_create.group_ids}")
    try:
        from services.user_service import UserService
        from models.user import UserCreate
        
        # Create the user
        new_user = UserService.create_user(UserCreate(
            email=user_create.email,
            full_name=user_create.full_name,
        ))
        
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user (email may already exist)"
            )
        
        # Add user to initial groups
        for group_id in user_create.group_ids:
            UserService.add_user_to_group(new_user.id, group_id)
        
        # Log the action
        AuditRepository.create({
            'user_id': current_user.id,
            'action': 'created_user',
            'changes': {
                'new_user_id': new_user.id,
                'email': new_user.email,
                'groups': user_create.group_ids
            },
            'metadata': {'operation': 'user_create'}
        })
        
        # Get groups for response
        group_ids = UserService.get_user_groups(new_user.id)
        groups = []
        for gid in group_ids:
            group = _get_chatbot_group_by_id(gid)
            if group:
                groups.append({
                    'id': group['id'],
                    'name': group['name'],
                    'description': group.get('description', '')
                })
        
        return AdminUserDetail(
            id=new_user.id,
            username=new_user.email.split('@')[0],
            email=new_user.email,
            full_name=new_user.full_name,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
            last_login=new_user.last_login,
            groups=groups
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.put("/users/{user_id}", response_model=AdminUserDetail)
async def update_user(
    user_id: int,
    user_update: AdminUserUpdate,
    current_user: User = Depends(require_admin)
):
    """Update user information (admin only)."""
    try:
        from services.user_service import UserService
        from models.user import UserUpdate as BaseUserUpdate
        
        # Get existing user
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update basic user info
        update_data = {}
        if user_update.email is not None:
            update_data['email'] = user_update.email
        if user_update.full_name is not None:
            update_data['full_name'] = user_update.full_name
        if user_update.is_active is not None:
            update_data['is_active'] = user_update.is_active
        
        if update_data:
            updated_user = UserService.update_user(user_id, BaseUserUpdate(**update_data))
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to update user"
                )
        else:
            updated_user = user
        
        # Log the action
        AuditRepository.create({
            'user_id': current_user.id,
            'action': 'updated_user',
            'changes': {
                'target_user_id': user_id,
                'updates': update_data,
            },
            'metadata': {'operation': 'user_update'}
        })
        
        # Get groups for response
        group_ids = UserService.get_user_groups(updated_user.id)
        groups = []
        for gid in group_ids:
            group = _get_chatbot_group_by_id(gid)
            if group:
                groups.append({
                    'id': group['id'],
                    'name': group['name'],
                    'description': group.get('description', '')
                })
        
        return AdminUserDetail(
            id=updated_user.id,
            username=updated_user.email.split('@')[0],
            email=updated_user.email,
            full_name=updated_user.full_name,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            last_login=updated_user.last_login,
            groups=groups
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.post("/users/{user_id}/groups/{group_id}")
async def assign_user_to_group(
    user_id: int,
    group_id: int,
    current_user: User = Depends(require_admin)
):
    """Assign user to a group (admin only)."""
    try:
        from services.user_service import UserService
        
        # Verify user exists
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify group exists
        group = _get_chatbot_group_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        success = UserService.add_user_to_group(user_id, group_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add user to group (may already be member)"
            )
        
        # Log the action
        AuditRepository.create({
            'user_id': current_user.id,
            'action': 'assigned_user_to_group',
            'changes': {
                'target_user_id': user_id,
                'group_id': group_id,
                'email': user.email,
                'group_name': group['name']
            },
            'metadata': {'operation': 'user_group_assignment'}
        })
        
        return {
            "success": True,
            "message": f"User {user.email} added to group {group['name']}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign user to group: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to assign user to group: {str(e)}")


@router.delete("/users/{user_id}/groups/{group_id}")
async def remove_user_from_group(
    user_id: int,
    group_id: int,
    current_user: User = Depends(require_admin)
):
    """Remove user from a group (admin only)."""
    try:
        from services.user_service import UserService
        
        # Verify user exists
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify group exists
        group = _get_chatbot_group_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        success = UserService.remove_user_from_group(user_id, group_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not in group or removal failed"
            )
        
        # Log the action
        AuditRepository.create({
            'user_id': current_user.id,
            'action': 'removed_user_from_group',
            'changes': {
                'target_user_id': user_id,
                'group_id': group_id,
                'email': user.email,
                'group_name': group['name']
            },
            'metadata': {'operation': 'user_group_removal'}
        })
        
        return {
            "success": True,
            "message": f"User {user.email} removed from group {group['name']}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove user from group: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove user from group: {str(e)}")


@router.get("/user-stats")
async def get_user_stats(
    current_user: User = Depends(require_admin)
):
    """Get user statistics for dashboard."""
    try:
        from services.user_service import UserService
        from database.connection import get_db_connection
        from datetime import datetime, timedelta
        
        all_users = UserService.get_all_users()
        total_users = len(all_users)
        
        # Query database directly for more reliable date filtering
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Count users created today (PostgreSQL syntax)
            cursor.execute("""
                SELECT COUNT(*) as count FROM users 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            result = cursor.fetchone()
            users_created_today = result['count'] if result else 0
            
            # Count active users in last week (with last_login, PostgreSQL syntax)
            cursor.execute("""
                SELECT COUNT(*) as count FROM users 
                WHERE last_login IS NOT NULL 
                AND last_login >= NOW() - INTERVAL '7 days'
            """)
            result = cursor.fetchone()
            active_users_last_week = result['count'] if result else 0
        
        return {
            "total_users": total_users,
            "users_created_today": users_created_today,
            "active_users_last_week": active_users_last_week
        }
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get user stats: {str(e)}")


@router.get("/sessions")
async def get_all_sessions(
    current_user: User = Depends(require_admin)
):
    """Get all active sessions for dashboard."""
    try:
        from database.connection import get_db_connection
        
        # Get all sessions from database with message counts
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT us.session_id, u.email, us.created_at, us.last_activity,
                       us.active_agent_id, us.active_corpora,
                       COALESCE(us.message_count, 0) as message_count,
                       COALESCE(us.user_query_count, 0) as user_query_count
                FROM user_sessions us
                LEFT JOIN users u ON us.user_id = u.id
                WHERE us.is_active = TRUE
                ORDER BY us.last_activity DESC
                LIMIT 100
            """)
            rows = cursor.fetchall()
        
        # Format sessions for frontend
        formatted_sessions = []
        for row in rows:
            formatted_sessions.append({
                "session_id": row['session_id'],
                "username": row['email'] if row['email'] else 'Unknown',
                "created_at": row['created_at'],
                "last_activity": row['last_activity'] if row['last_activity'] else row['created_at'],
                "chat_messages": row['message_count'],
                "user_queries": row['user_query_count'],
                "agent_id": row['active_agent_id'],
                "active_corpora": row['active_corpora']
            })
        
        return formatted_sessions
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}")
        # Return empty list if sessions not available (table might not exist yet)
        return []


@router.get("/active-session-board")
async def get_active_session_board(
    current_user: User = Depends(require_admin)
):
    """
    Get active session data for the Active Session Board dashboard.
    Returns time-bucketed user activity, session details, and summary stats.
    """
    try:
        from database.connection import get_db_connection
        from datetime import datetime, timezone
        from services.session_service import SESSION_IDLE_HOURS

        idle_interval = f'{SESSION_IDLE_HOURS} hours'

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get latest active session per user with aggregated counts
            cursor.execute("""
                SELECT latest.session_id, latest.user_id,
                       latest.email, latest.full_name,
                       latest.created_at, latest.last_activity,
                       latest.agent_name, latest.agent_key,
                       latest.active_corpora,
                       agg.total_messages as message_count,
                       agg.total_queries as user_query_count,
                       agg.session_count
                FROM (
                    SELECT DISTINCT ON (us.user_id)
                           us.session_id, us.user_id,
                           u.email, u.full_name,
                           us.created_at, us.last_activity,
                           a.display_name as agent_name, a.name as agent_key,
                           us.active_corpora
                    FROM user_sessions us
                    LEFT JOIN users u ON us.user_id = u.id
                    LEFT JOIN agents a ON us.active_agent_id = a.id
                    WHERE us.is_active = TRUE
                      AND us.last_activity >= NOW() - INTERVAL '%s'
                    ORDER BY us.user_id, us.last_activity DESC NULLS LAST
                ) latest
                LEFT JOIN (
                    SELECT user_id,
                           COALESCE(SUM(message_count), 0) as total_messages,
                           COALESCE(SUM(user_query_count), 0) as total_queries,
                           COUNT(*) as session_count
                    FROM user_sessions
                    WHERE is_active = TRUE
                      AND last_activity >= NOW() - INTERVAL '%s'
                    GROUP BY user_id
                ) agg ON latest.user_id = agg.user_id
                ORDER BY latest.last_activity DESC NULLS LAST
            """, (idle_interval, idle_interval))
            sessions = [dict(row) for row in cursor.fetchall()]

            # Get time-bucketed counts using database timestamps
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE us.last_activity >= NOW() - INTERVAL '5 minutes') as active_5m,
                    COUNT(*) FILTER (WHERE us.last_activity >= NOW() - INTERVAL '10 minutes') as active_10m,
                    COUNT(*) FILTER (WHERE us.last_activity >= NOW() - INTERVAL '30 minutes') as active_30m,
                    COUNT(*) FILTER (WHERE us.last_activity >= NOW() - INTERVAL '60 minutes') as active_60m,
                    COUNT(*) as total_active,
                    COALESCE(SUM(us.message_count), 0) as total_messages,
                    COALESCE(SUM(us.user_query_count), 0) as total_queries,
                    COUNT(*) FILTER (WHERE DATE(us.created_at) = CURRENT_DATE) as sessions_created_today,
                    COUNT(DISTINCT us.user_id) FILTER (WHERE us.last_activity >= NOW() - INTERVAL '5 minutes') as users_5m,
                    COUNT(DISTINCT us.user_id) FILTER (WHERE us.last_activity >= NOW() - INTERVAL '10 minutes') as users_10m,
                    COUNT(DISTINCT us.user_id) FILTER (WHERE us.last_activity >= NOW() - INTERVAL '30 minutes') as users_30m,
                    COUNT(DISTINCT us.user_id) FILTER (WHERE us.last_activity >= NOW() - INTERVAL '60 minutes') as users_60m,
                    COUNT(DISTINCT us.user_id) as total_users_with_sessions
                FROM user_sessions us
                WHERE us.is_active = TRUE
                  AND us.last_activity >= NOW() - INTERVAL '%s'
            """, (idle_interval,))
            stats_row = cursor.fetchone()

            # Get total registered users count
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = TRUE")
            total_users = cursor.fetchone()['count']

        now = datetime.now(timezone.utc)

        # Format sessions with relative time info
        formatted_sessions = []
        for s in sessions:
            last_activity = s['last_activity'] or s['created_at']
            created_at = s['created_at']

            # Calculate seconds ago for frontend relative time
            if isinstance(last_activity, str):
                last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            else:
                last_activity_dt = last_activity if last_activity.tzinfo else last_activity.replace(tzinfo=timezone.utc)

            if isinstance(created_at, str):
                created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_at_dt = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)

            seconds_ago = max(0, int((now - last_activity_dt).total_seconds()))
            duration_seconds = max(0, int((now - created_at_dt).total_seconds()))

            formatted_sessions.append({
                "session_id": s['session_id'],
                "user_id": s['user_id'],
                "username": s['email'] or 'Unknown',
                "email": s['email'] or '',
                "full_name": s['full_name'] or '',
                "created_at": str(created_at),
                "last_activity": str(last_activity),
                "seconds_ago": seconds_ago,
                "duration_seconds": duration_seconds,
                "agent_name": s['agent_name'] or 'Default',
                "agent_key": s['agent_key'] or '',
                "active_corpora": s['active_corpora'] or [],
                "message_count": s['message_count'],
                "user_query_count": s['user_query_count'],
                "session_count": s.get('session_count', 1),
            })

        stats = dict(stats_row) if stats_row else {}

        return {
            "sessions": formatted_sessions,
            "summary": {
                "users_5m": stats.get('users_5m', 0),
                "users_10m": stats.get('users_10m', 0),
                "users_30m": stats.get('users_30m', 0),
                "users_60m": stats.get('users_60m', 0),
                "total_active_sessions": stats.get('total_active', 0),
                "total_users_with_sessions": stats.get('total_users_with_sessions', 0),
                "total_registered_users": total_users,
                "sessions_created_today": stats.get('sessions_created_today', 0),
                "total_messages": stats.get('total_messages', 0),
                "total_queries": stats.get('total_queries', 0),
            },
            "server_time": now.isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get active session board data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load session board: {str(e)}")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin)
):
    """Delete (deactivate) a user (admin only)."""
    try:
        from services.user_service import UserService
        from models.user import UserUpdate as BaseUserUpdate
        
        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Get existing user
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Deactivate the user
        updated_user = UserService.update_user(
            user_id,
            BaseUserUpdate(is_active=False)
        )
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to deactivate user"
            )
        
        # Log the action
        AuditRepository.create({
            'user_id': current_user.id,
            'action': 'deleted_user',
            'changes': {
                'target_user_id': user_id,
                'email': user.email
            },
            'metadata': {'operation': 'user_delete'}
        })
        
        return {
            "success": True,
            "message": f"User {user.email} has been deactivated"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


# ========== Agent Assignment Management ==========

@router.get("/agent-assignments")
async def list_user_agent_assignments(
    current_user: User = Depends(require_admin)
):
    """Get all users with their agent assignments."""
    try:
        from database.connection import get_db_connection
        from services.agent_loader import load_agent_config
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        u.id, u.email, u.full_name, u.is_active,
                        u.default_agent_id,
                        a.id as agent_id, a.name as agent_name, 
                        a.display_name as agent_display_name,
                        a.config_path
                    FROM users u
                    LEFT JOIN agents a ON u.default_agent_id = a.id
                    WHERE u.is_active = true
                    ORDER BY u.email
                """)
                users = cur.fetchall()
                
                # Get all agent access for each user
                cur.execute("""
                    SELECT uaa.user_id, a.id as agent_id, a.name, a.display_name, a.config_path
                    FROM user_agent_access uaa
                    JOIN agents a ON uaa.agent_id = a.id
                    WHERE a.is_active = true
                    ORDER BY uaa.user_id, a.id
                """)
                access_rows = cur.fetchall()
        
        # Group access by user_id
        access_by_user = {}
        for row in access_rows:
            uid = row['user_id']
            if uid not in access_by_user:
                access_by_user[uid] = []
            access_by_user[uid].append({
                'id': row['agent_id'],
                'name': row['name'],
                'display_name': row['display_name'],
                'config_path': row['config_path'],
            })
        
        result = []
        for u in users:
            result.append({
                'id': u['id'],
                'username': u['email'].split('@')[0] if u['email'] else '',
                'email': u['email'],
                'full_name': u['full_name'],
                'is_active': u['is_active'],
                'default_agent': {
                    'id': u['agent_id'],
                    'name': u['agent_name'],
                    'display_name': u['agent_display_name'],
                    'config_path': u['config_path'],
                } if u['agent_id'] else None,
                'accessible_agents': access_by_user.get(u['id'], []),
            })
        
        return result
    except Exception as e:
        logger.error(f"Failed to list agent assignments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents-list")
async def list_all_agents_admin(
    current_user: User = Depends(require_admin)
):
    """Get all agents with their tools (for admin assignment UI)."""
    try:
        from services.agent_service import AgentService
        from services.agent_loader import load_agent_config
        
        agents = AgentService.get_all_agents(active_only=True)
        result = []
        for agent in agents:
            tools = []
            agent_type = None
            try:
                config = load_agent_config(agent.config_path)
                tools = config.get('tools', [])
                agent_type = config.get('agent_name', agent.config_path)
            except Exception:
                pass
            
            result.append({
                'id': agent.id,
                'name': agent.name,
                'display_name': agent.display_name,
                'description': agent.description,
                'config_path': agent.config_path,
                'agent_type': agent_type,
                'tools': tools,
            })
        
        return result
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}/default-agent/{agent_id}")
async def admin_set_user_default_agent(
    user_id: int,
    agent_id: int,
    current_user: User = Depends(require_admin)
):
    """Set a user's default agent (admin only)."""
    try:
        from services.agent_service import AgentService
        from services.user_service import UserService
        
        # Verify user exists
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify agent exists
        agent = AgentService.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Grant access if not already granted
        if not AgentService.validate_agent_access(user_id, agent_id):
            AgentService.grant_user_access(user_id, agent_id)
            logger.info(f"Auto-granted user {user_id} access to agent {agent_id}")
        
        # Set default agent
        success = UserService.set_default_agent(user_id, agent_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to set default agent")
        
        # Log the action
        AuditRepository.create({
            'user_id': current_user.id,
            'action': 'set_user_default_agent',
            'changes': {
                'target_user_id': user_id,
                'target_email': user.email,
                'agent_id': agent_id,
                'agent_name': agent.name,
            },
            'metadata': {'operation': 'agent_assignment'}
        })
        
        logger.info(f"Admin {current_user.email} set user {user.email} default agent to {agent.name}")
        return {
            "success": True,
            "message": f"Set {user.email}'s default agent to {agent.display_name}",
            "user_id": user_id,
            "agent_id": agent_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set default agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/agent-access/{agent_id}")
async def admin_grant_agent_access(
    user_id: int,
    agent_id: int,
    current_user: User = Depends(require_admin)
):
    """Grant a user access to an agent (admin only)."""
    try:
        from services.agent_service import AgentService
        from services.user_service import UserService
        
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        agent = AgentService.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        success = AgentService.grant_user_access(user_id, agent_id)
        if not success:
            return {"success": True, "message": "User already has access"}
        
        logger.info(f"Admin {current_user.email} granted user {user.email} access to agent {agent.name}")
        return {"success": True, "message": f"Granted {user.email} access to {agent.display_name}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to grant agent access: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}/agent-access/{agent_id}")
async def admin_revoke_agent_access(
    user_id: int,
    agent_id: int,
    current_user: User = Depends(require_admin)
):
    """Revoke a user's access to an agent (admin only)."""
    try:
        from services.agent_service import AgentService
        from services.user_service import UserService
        
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Don't allow revoking access to the user's default agent
        if user.default_agent_id == agent_id:
            raise HTTPException(
                status_code=400, 
                detail="Cannot revoke access to user's default agent. Change default agent first."
            )
        
        success = AgentService.revoke_user_access(user_id, agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Access not found")
        
        logger.info(f"Admin {current_user.email} revoked user {user.email} access to agent {agent_id}")
        return {"success": True, "message": "Access revoked"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke agent access: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/access-matrix")
async def get_access_matrix(current_user: User = Depends(require_admin)):
    """Get access matrix data showing agent assignments and corpus access for all chatbot users.
    
    Returns:
        - users: List of active chatbot users with their details
        - agents: List of available agents
        - corpora: List of active corpora
        - agent_assignments: Map of user_id -> agent_id
        - corpus_access: Map of user_id -> list of corpus_ids
    """
    try:
        from database.connection import get_db_connection
        from services.agent_service import AgentService
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all active chatbot users with their assigned groups and agents
            cursor.execute("""
                SELECT 
                    cu.id as chatbot_user_id,
                    cu.email,
                    cu.full_name,
                    cg.name as chatbot_group_name,
                    cg.id as chatbot_group_id,
                    a.id as agent_id,
                    a.name as agent_key,
                    a.display_name as agent_name
                FROM chatbot_users cu
                LEFT JOIN chatbot_user_groups cug ON cu.id = cug.chatbot_user_id
                LEFT JOIN chatbot_groups cg ON cug.chatbot_group_id = cg.id
                LEFT JOIN chatbot_group_agents cga ON cg.id = cga.group_id
                LEFT JOIN chatbot_agents a ON cga.agent_id = a.id
                WHERE cu.is_active = TRUE
                ORDER BY cu.email
            """)
            user_agent_rows = cursor.fetchall()
            
            # Get all available chatbot agents
            cursor.execute("""
                SELECT id, name, display_name, description, is_active
                FROM chatbot_agents
                WHERE is_active = TRUE
                ORDER BY display_name
            """)
            agent_rows = cursor.fetchall()
            
            # Get all active corpora
            cursor.execute("""
                SELECT id, name, display_name, description, is_active
                FROM corpora
                WHERE is_active = TRUE
                ORDER BY display_name
            """)
            corpus_rows = cursor.fetchall()
            
            # Get corpus access for all chatbot users
            cursor.execute("""
                SELECT 
                    cu.id as chatbot_user_id,
                    cca.corpus_id,
                    c.name as corpus_name,
                    c.display_name as corpus_display_name
                FROM chatbot_users cu
                LEFT JOIN chatbot_user_groups cug ON cu.id = cug.chatbot_user_id
                LEFT JOIN chatbot_corpus_access cca ON cug.chatbot_group_id = cca.chatbot_group_id
                LEFT JOIN corpora c ON cca.corpus_id = c.id
                WHERE cu.is_active = TRUE AND c.is_active = TRUE
                ORDER BY cu.id, c.display_name
            """)
            corpus_access_rows = cursor.fetchall()
        
        # Build user list (deduplicated)
        users_map = {}
        for row in user_agent_rows:
            chatbot_user_id = row['chatbot_user_id']
            if chatbot_user_id not in users_map:
                users_map[chatbot_user_id] = {
                    'chatbot_user_id': chatbot_user_id,
                    'email': row['email'],
                    'full_name': row['full_name'],
                    'chatbot_group_name': row['chatbot_group_name'],
                    'chatbot_group_id': row['chatbot_group_id']
                }
        
        users = list(users_map.values())
        
        # Build agents list
        agents = [
            {
                'id': row['id'],
                'name': row['name'],
                'display_name': row['display_name'],
                'description': row['description']
            }
            for row in agent_rows
        ]
        
        # Build corpora list
        corpora = [
            {
                'id': row['id'],
                'name': row['name'],
                'display_name': row['display_name'],
                'description': row['description']
            }
            for row in corpus_rows
        ]
        
        # Build agent assignments map (chatbot_user_id -> agent_id)
        agent_assignments = {}
        for row in user_agent_rows:
            chatbot_user_id = row['chatbot_user_id']
            agent_id = row['agent_id']
            if agent_id:  # Only include if agent is assigned
                agent_assignments[chatbot_user_id] = agent_id
        
        # Build corpus access map (chatbot_user_id -> [corpus_ids])
        corpus_access = {}
        for row in corpus_access_rows:
            chatbot_user_id = row['chatbot_user_id']
            corpus_id = row['corpus_id']
            if corpus_id:  # Only include if corpus exists
                if chatbot_user_id not in corpus_access:
                    corpus_access[chatbot_user_id] = []
                corpus_access[chatbot_user_id].append(corpus_id)
        
        return {
            'users': users,
            'agents': agents,
            'corpora': corpora,
            'agent_assignments': agent_assignments,
            'corpus_access': corpus_access
        }
        
    except Exception as e:
        logger.error(f"Failed to get access matrix: {e}")
        raise HTTPException(status_code=500, detail=str(e))
