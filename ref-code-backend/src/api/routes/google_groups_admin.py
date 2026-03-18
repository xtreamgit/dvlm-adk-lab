"""
Admin API endpoints for managing Google Groups Bridge mappings.

Provides CRUD for:
- Google Group → Chatbot Group (agent type) mappings
- Google Group → Corpus access mappings
- Bridge status and manual sync triggers
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging

from middleware.iap_auth_middleware import get_current_user_iap
from models.user import User
from database.connection import get_db_connection
from services.google_groups_bridge import GoogleGroupsBridge
from services.google_groups_service import GoogleGroupsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/google-groups", tags=["Google Groups Admin"])


# ============================================================================
# Pydantic Models
# ============================================================================

class AgentMappingCreate(BaseModel):
    google_group_email: str = Field(..., min_length=3, max_length=255)
    chatbot_group_id: int
    priority: int = 0

class AgentMappingUpdate(BaseModel):
    chatbot_group_id: Optional[int] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class AgentMappingResponse(BaseModel):
    id: int
    google_group_email: str
    chatbot_group_id: int
    chatbot_group_name: Optional[str] = None
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class CorpusMappingCreate(BaseModel):
    google_group_email: str = Field(..., min_length=3, max_length=255)
    corpus_id: int
    permission: str = "query"

class CorpusMappingUpdate(BaseModel):
    permission: Optional[str] = None
    is_active: Optional[bool] = None

class CorpusMappingResponse(BaseModel):
    id: int
    google_group_email: str
    corpus_id: int
    corpus_name: Optional[str] = None
    permission: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class BridgeStatusResponse(BaseModel):
    enabled: bool
    cache_ttl_seconds: int = 0
    agent_mappings_count: int = 0
    corpus_mappings_count: int = 0
    synced_users_count: int = 0
    last_sync: Optional[str] = None

class SyncResultResponse(BaseModel):
    user_id: int
    email: str
    google_groups: List[str] = []
    chatbot_group: Optional[str] = None
    corpora_synced: int = 0
    from_cache: bool = False
    status: str


# ============================================================================
# Agent Mapping Endpoints
# ============================================================================

@router.get("/agent-mappings", response_model=List[AgentMappingResponse])
async def list_agent_mappings(current_user: User = Depends(get_current_user_iap)):
    """List all Google Group → Chatbot Group mappings."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ggam.*, cg.name as chatbot_group_name
                FROM google_group_agent_mappings ggam
                LEFT JOIN chatbot_groups cg ON ggam.chatbot_group_id = cg.id
                ORDER BY ggam.priority DESC, ggam.google_group_email
            """)
            rows = cursor.fetchall()
            return [AgentMappingResponse(**dict(row)) for row in rows]
    except Exception as e:
        logger.error(f"Failed to list agent mappings: {e}")
        raise HTTPException(status_code=500, detail="Failed to list agent mappings")


@router.post("/agent-mappings", response_model=AgentMappingResponse, status_code=201)
async def create_agent_mapping(
    mapping: AgentMappingCreate,
    current_user: User = Depends(get_current_user_iap),
):
    """Create a new Google Group → Chatbot Group mapping."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Verify chatbot_group exists
            cursor.execute(
                "SELECT id, name FROM chatbot_groups WHERE id = %s",
                (mapping.chatbot_group_id,),
            )
            group = cursor.fetchone()
            if not group:
                raise HTTPException(
                    status_code=404,
                    detail=f"Chatbot group {mapping.chatbot_group_id} not found",
                )

            cursor.execute(
                """
                INSERT INTO google_group_agent_mappings
                    (google_group_email, chatbot_group_id, priority, created_by)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (
                    mapping.google_group_email,
                    mapping.chatbot_group_id,
                    mapping.priority,
                    current_user.id,
                ),
            )
            row = cursor.fetchone()
            conn.commit()

            result = dict(row)
            result["chatbot_group_name"] = group["name"]
            return AgentMappingResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail=f"Mapping for {mapping.google_group_email} already exists",
            )
        logger.error(f"Failed to create agent mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to create agent mapping")


@router.put("/agent-mappings/{mapping_id}", response_model=AgentMappingResponse)
async def update_agent_mapping(
    mapping_id: int,
    update: AgentMappingUpdate,
    current_user: User = Depends(get_current_user_iap),
):
    """Update a Google Group → Chatbot Group mapping."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update
            updates = {}
            if update.chatbot_group_id is not None:
                updates["chatbot_group_id"] = update.chatbot_group_id
            if update.priority is not None:
                updates["priority"] = update.priority
            if update.is_active is not None:
                updates["is_active"] = update.is_active

            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")

            updates["updated_at"] = "CURRENT_TIMESTAMP"
            set_parts = []
            values = []
            for key, val in updates.items():
                if val == "CURRENT_TIMESTAMP":
                    set_parts.append(f"{key} = CURRENT_TIMESTAMP")
                else:
                    set_parts.append(f"{key} = %s")
                    values.append(val)

            values.append(mapping_id)
            cursor.execute(
                f"""
                UPDATE google_group_agent_mappings
                SET {', '.join(set_parts)}
                WHERE id = %s
                RETURNING *
                """,
                values,
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Mapping not found")

            # Get group name
            cursor.execute(
                "SELECT name FROM chatbot_groups WHERE id = %s",
                (row["chatbot_group_id"],),
            )
            group = cursor.fetchone()
            conn.commit()

            result = dict(row)
            result["chatbot_group_name"] = group["name"] if group else None
            return AgentMappingResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update agent mapping")


@router.delete("/agent-mappings/{mapping_id}", status_code=204)
async def delete_agent_mapping(
    mapping_id: int,
    current_user: User = Depends(get_current_user_iap),
):
    """Delete a Google Group → Chatbot Group mapping."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM google_group_agent_mappings WHERE id = %s RETURNING id",
                (mapping_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Mapping not found")
            conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete agent mapping")


# ============================================================================
# Corpus Mapping Endpoints
# ============================================================================

@router.get("/corpus-mappings", response_model=List[CorpusMappingResponse])
async def list_corpus_mappings(current_user: User = Depends(get_current_user_iap)):
    """List all Google Group → Corpus access mappings."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ggcm.*, c.name as corpus_name
                FROM google_group_corpus_mappings ggcm
                LEFT JOIN corpora c ON ggcm.corpus_id = c.id
                ORDER BY ggcm.google_group_email, c.name
            """)
            rows = cursor.fetchall()
            return [CorpusMappingResponse(**dict(row)) for row in rows]
    except Exception as e:
        logger.error(f"Failed to list corpus mappings: {e}")
        raise HTTPException(status_code=500, detail="Failed to list corpus mappings")


@router.post("/corpus-mappings", response_model=CorpusMappingResponse, status_code=201)
async def create_corpus_mapping(
    mapping: CorpusMappingCreate,
    current_user: User = Depends(get_current_user_iap),
):
    """Create a new Google Group → Corpus access mapping."""
    valid_permissions = {"query", "read", "upload", "delete", "admin"}
    if mapping.permission not in valid_permissions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid permission. Must be one of: {', '.join(sorted(valid_permissions))}",
        )

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Verify corpus exists
            cursor.execute(
                "SELECT id, name FROM corpora WHERE id = %s",
                (mapping.corpus_id,),
            )
            corpus = cursor.fetchone()
            if not corpus:
                raise HTTPException(
                    status_code=404,
                    detail=f"Corpus {mapping.corpus_id} not found",
                )

            cursor.execute(
                """
                INSERT INTO google_group_corpus_mappings
                    (google_group_email, corpus_id, permission, created_by)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (
                    mapping.google_group_email,
                    mapping.corpus_id,
                    mapping.permission,
                    current_user.id,
                ),
            )
            row = cursor.fetchone()
            conn.commit()

            result = dict(row)
            result["corpus_name"] = corpus["name"]
            return CorpusMappingResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail=f"Mapping for {mapping.google_group_email} + corpus {mapping.corpus_id} already exists",
            )
        logger.error(f"Failed to create corpus mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to create corpus mapping")


@router.put("/corpus-mappings/{mapping_id}", response_model=CorpusMappingResponse)
async def update_corpus_mapping(
    mapping_id: int,
    update: CorpusMappingUpdate,
    current_user: User = Depends(get_current_user_iap),
):
    """Update a Google Group → Corpus access mapping."""
    if update.permission is not None:
        valid_permissions = {"query", "read", "upload", "delete", "admin"}
        if update.permission not in valid_permissions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid permission. Must be one of: {', '.join(sorted(valid_permissions))}",
            )

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            updates = {}
            if update.permission is not None:
                updates["permission"] = update.permission
            if update.is_active is not None:
                updates["is_active"] = update.is_active

            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")

            set_parts = ["updated_at = CURRENT_TIMESTAMP"]
            values = []
            for key, val in updates.items():
                set_parts.append(f"{key} = %s")
                values.append(val)

            values.append(mapping_id)
            cursor.execute(
                f"""
                UPDATE google_group_corpus_mappings
                SET {', '.join(set_parts)}
                WHERE id = %s
                RETURNING *
                """,
                values,
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Mapping not found")

            # Get corpus name
            cursor.execute(
                "SELECT name FROM corpora WHERE id = %s",
                (row["corpus_id"],),
            )
            corpus = cursor.fetchone()
            conn.commit()

            result = dict(row)
            result["corpus_name"] = corpus["name"] if corpus else None
            return CorpusMappingResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update corpus mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update corpus mapping")


@router.delete("/corpus-mappings/{mapping_id}", status_code=204)
async def delete_corpus_mapping(
    mapping_id: int,
    current_user: User = Depends(get_current_user_iap),
):
    """Delete a Google Group → Corpus access mapping."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM google_group_corpus_mappings WHERE id = %s RETURNING id",
                (mapping_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Mapping not found")
            conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete corpus mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete corpus mapping")


# ============================================================================
# Status & Sync Endpoints
# ============================================================================

@router.get("/status", response_model=BridgeStatusResponse)
async def get_bridge_status(current_user: User = Depends(get_current_user_iap)):
    """Get the current status of the Google Groups Bridge."""
    return BridgeStatusResponse(**GoogleGroupsBridge.get_bridge_status())


@router.post("/sync/{user_id}", response_model=SyncResultResponse)
async def sync_user(
    user_id: int,
    current_user: User = Depends(get_current_user_iap),
):
    """Force re-sync a specific user's Google Groups."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        result = await GoogleGroupsBridge.force_sync_user(user["id"], user["email"])
        return SyncResultResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync user")


@router.post("/sync-all", response_model=List[SyncResultResponse])
async def sync_all_users(current_user: User = Depends(get_current_user_iap)):
    """Force re-sync all active users whose email matches the org domain."""
    try:
        # Derive org domain from available env vars
        import os
        org_domain = os.getenv("GOOGLE_GROUPS_ORG_DOMAIN", "")
        if not org_domain:
            # Fallback: derive from GOOGLE_GROUPS_ADMIN_EMAIL or IAP_DEV_USER_EMAIL
            for env_key in ("GOOGLE_GROUPS_ADMIN_EMAIL", "IAP_DEV_USER_EMAIL"):
                email = os.getenv(env_key, "")
                if "@" in email:
                    org_domain = email.split("@")[1]
                    break
        if not org_domain:
            raise HTTPException(
                status_code=500,
                detail="Cannot determine org domain. Set GOOGLE_GROUPS_ORG_DOMAIN, "
                       "GOOGLE_GROUPS_ADMIN_EMAIL, or IAP_DEV_USER_EMAIL.",
            )

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email FROM users WHERE is_active = TRUE AND email LIKE %s",
                (f"%@{org_domain}",),
            )
            users = cursor.fetchall()

        results = []
        for user in users:
            try:
                result = await GoogleGroupsBridge.force_sync_user(user["id"], user["email"])
                results.append(SyncResultResponse(**result))
            except Exception as e:
                results.append(
                    SyncResultResponse(
                        user_id=user["id"],
                        email=user["email"],
                        status=f"error: {str(e)}",
                    )
                )

        # After syncing all users, clean up stale corpus access entries
        cleanup = GoogleGroupsBridge.cleanup_stale_corpus_access()
        if cleanup.get("entries_removed", 0) > 0:
            logger.info(f"Post-sync cleanup: {cleanup}")

        return results

    except Exception as e:
        logger.error(f"Failed to sync all users: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync all users")


@router.post("/cleanup-corpus-access")
async def cleanup_corpus_access(current_user: User = Depends(get_current_user_iap)):
    """
    Remove stale corpus access entries not backed by any member's Google Groups.
    This makes Google Groups the single source of truth for bridge-managed groups.
    """
    try:
        result = GoogleGroupsBridge.cleanup_stale_corpus_access()
        return result
    except Exception as e:
        logger.error(f"Failed to cleanup corpus access: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup corpus access")
