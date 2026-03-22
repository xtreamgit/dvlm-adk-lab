"""
Chatbot Admin API Routes

These routes manage chatbot users, groups, roles, and permissions.
Chatbot users are separate from app managers - they are the users who
interact with the chatbot and have access to corpora and agents.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import logging

from middleware.iap_auth_middleware import get_current_user_iap as get_current_user
from database.connection import get_db_connection
from services.agent_hierarchy import (
    get_agent_type_hierarchy_list,
    get_all_tools_for_agent_type,
    AgentType,
    validate_agent_type,
    can_agent_type_use_tool
)
from middleware.tool_permission_middleware import (
    get_user_agent_type,
    get_user_allowed_tools
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/chatbot", tags=["Chatbot Admin"])


@router.get("/debug/user-link")
async def debug_user_link(current_user = Depends(get_current_user)):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, email, user_id, created_by FROM chatbot_users WHERE user_id = %s",
                (current_user.id,),
            )
            linked_by_user_id = cur.fetchone()

            cur.execute(
                "SELECT id, username, email, user_id, created_by FROM chatbot_users WHERE email = %s",
                (current_user.email,),
            )
            linked_by_email = cur.fetchone()

            chatbot_user_id = None
            if linked_by_user_id:
                chatbot_user_id = linked_by_user_id["id"]
            elif linked_by_email:
                chatbot_user_id = linked_by_email["id"]

            groups = []
            if chatbot_user_id:
                cur.execute(
                    """
                    SELECT cg.id, cg.name
                    FROM chatbot_groups cg
                    JOIN chatbot_user_groups cug ON cg.id = cug.chatbot_group_id
                    WHERE cug.chatbot_user_id = %s
                    ORDER BY cg.name
                    """,
                    (chatbot_user_id,),
                )
                groups = [dict(r) for r in cur.fetchall()]

            accessible_corpora = []
            if chatbot_user_id:
                cur.execute(
                    """
                    SELECT DISTINCT c.id, c.name, cca.permission
                    FROM corpora c
                    JOIN chatbot_corpus_access cca ON c.id = cca.corpus_id
                    JOIN chatbot_user_groups cug ON cca.chatbot_group_id = cug.chatbot_group_id
                    WHERE cug.chatbot_user_id = %s
                      AND c.is_active = TRUE
                    ORDER BY c.name
                    """,
                    (chatbot_user_id,),
                )
                accessible_corpora = [dict(r) for r in cur.fetchall()]

            return {
                "current_user": {
                    "id": current_user.id,
                    "email": current_user.email,
                },
                "chatbot_users": {
                    "linked_by_user_id": dict(linked_by_user_id) if linked_by_user_id else None,
                    "linked_by_email": dict(linked_by_email) if linked_by_email else None,
                },
                "groups": groups,
                "accessible_corpora": accessible_corpora,
            }


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatbotUserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: Optional[str] = None
    notes: Optional[str] = None
    group_ids: Optional[List[int]] = []


class ChatbotUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    notes: Optional[str] = None


class ChatbotUserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    notes: Optional[str] = None
    groups: List[dict] = []


class ChatbotGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ChatbotGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ChatbotGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    roles: List[dict] = []
    user_count: int = 0


class ChatbotRoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = []


class ChatbotRoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ChatbotRoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    permissions: List[dict] = []


class ChatbotPermissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: str


class ChatbotCorpusAccessCreate(BaseModel):
    chatbot_group_id: int
    corpus_id: int
    permission: str = "query"


class ChatbotAgentAccessCreate(BaseModel):
    chatbot_group_id: int
    agent_id: int
    can_use: bool = True


class ChatbotAgentResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    agent_type: str
    tools: List[str]
    is_active: bool
    created_at: datetime


# ============================================================================
# Helper Functions
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# ============================================================================
# Chatbot Users Endpoints
# ============================================================================

@router.get("/users", response_model=List[ChatbotUserResponse])
async def get_all_chatbot_users(current_user: dict = Depends(get_current_user)):
    """Get all chatbot users with their groups"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cu.id, cu.username, cu.email, cu.full_name, cu.is_active,
                       cu.created_at, cu.updated_at, cu.last_login, cu.notes
                FROM chatbot_users cu
                ORDER BY cu.created_at DESC
            """)
            users = cur.fetchall()
            
            result = []
            for user in users:
                # Get groups for each user
                cur.execute("""
                    SELECT cg.id, cg.name, cg.description
                    FROM chatbot_groups cg
                    JOIN chatbot_user_groups cug ON cg.id = cug.chatbot_group_id
                    WHERE cug.chatbot_user_id = %s
                """, (user['id'],))
                groups = [{"id": g['id'], "name": g['name'], "description": g['description']} for g in cur.fetchall()]
                
                result.append({
                    "id": user['id'],
                    "username": user['username'],
                    "email": user['email'],
                    "full_name": user['full_name'],
                    "is_active": user['is_active'],
                    "created_at": user['created_at'],
                    "updated_at": user['updated_at'],
                    "last_login": user['last_login'],
                    "notes": user['notes'],
                    "groups": groups
                })
            
            return result


@router.post("/users", response_model=ChatbotUserResponse, status_code=status.HTTP_201_CREATED)
async def create_chatbot_user(
    user_data: ChatbotUserCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new chatbot user"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check if username or email already exists
            cur.execute(
                "SELECT id FROM chatbot_users WHERE username = %s OR email = %s",
                (user_data.username, user_data.email)
            )
            if cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already exists"
                )
            
            # Hash password if provided
            hashed_password = None
            if user_data.password:
                hashed_password = hash_password(user_data.password)
            
            # Create user
            cur.execute("""
                INSERT INTO chatbot_users (username, email, full_name, hashed_password, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, username, email, full_name, is_active, created_at, updated_at, last_login, notes
            """, (
                user_data.username,
                user_data.email,
                user_data.full_name,
                hashed_password,
                user_data.notes,
                current_user.id
            ))
            user = cur.fetchone()
            
            # Assign to groups
            groups = []
            if user_data.group_ids:
                for group_id in user_data.group_ids:
                    cur.execute("""
                        INSERT INTO chatbot_user_groups (chatbot_user_id, chatbot_group_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (user['id'], group_id))
                
                # Get group details
                cur.execute("""
                    SELECT cg.id, cg.name, cg.description
                    FROM chatbot_groups cg
                    WHERE cg.id = ANY(%s)
                """, (user_data.group_ids,))
                groups = [{"id": g['id'], "name": g['name'], "description": g['description']} for g in cur.fetchall()]
            
            conn.commit()
            
            return {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "full_name": user['full_name'],
                "is_active": user['is_active'],
                "created_at": user['created_at'],
                "updated_at": user['updated_at'],
                "last_login": user['last_login'],
                "notes": user['notes'],
                "groups": groups
            }


@router.put("/users/{user_id}", response_model=ChatbotUserResponse)
async def update_chatbot_user(
    user_id: int,
    user_data: ChatbotUserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a chatbot user"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Build update query dynamically
            updates = []
            values = []
            
            if user_data.email is not None:
                updates.append("email = %s")
                values.append(user_data.email)
            if user_data.full_name is not None:
                updates.append("full_name = %s")
                values.append(user_data.full_name)
            if user_data.is_active is not None:
                updates.append("is_active = %s")
                values.append(user_data.is_active)
            if user_data.password is not None:
                updates.append("hashed_password = %s")
                values.append(hash_password(user_data.password))
            if user_data.notes is not None:
                updates.append("notes = %s")
                values.append(user_data.notes)
            
            if not updates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            
            query = f"""
                UPDATE chatbot_users SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, username, email, full_name, is_active, created_at, updated_at, last_login, notes
            """
            
            cur.execute(query, values)
            user = cur.fetchone()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chatbot user not found"
                )
            
            # Get groups
            cur.execute("""
                SELECT cg.id, cg.name, cg.description
                FROM chatbot_groups cg
                JOIN chatbot_user_groups cug ON cg.id = cug.chatbot_group_id
                WHERE cug.chatbot_user_id = %s
            """, (user['id'],))
            groups = [{"id": g['id'], "name": g['name'], "description": g['description']} for g in cur.fetchall()]
            
            conn.commit()
            
            return {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "full_name": user['full_name'],
                "is_active": user['is_active'],
                "created_at": user['created_at'],
                "updated_at": user['updated_at'],
                "last_login": user['last_login'],
                "notes": user['notes'],
                "groups": groups
            }


@router.delete("/users/{user_id}")
async def delete_chatbot_user(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Deactivate a chatbot user (soft delete)"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE chatbot_users SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id
            """, (user_id,))
            
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chatbot user not found"
                )
            
            conn.commit()
            return {"status": "success", "message": "Chatbot user deactivated"}


@router.delete("/users/{user_id}/permanent")
async def permanently_delete_chatbot_user(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Permanently delete a chatbot user. User must be inactive first."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Verify user exists and is inactive
            cur.execute(
                "SELECT id, username, is_active FROM chatbot_users WHERE id = %s",
                (user_id,)
            )
            user = cur.fetchone()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chatbot user not found"
                )

            if user['is_active']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete an active user. Deactivate the user first."
                )

            username = user['username']

            # Delete user (chatbot_user_groups will cascade automatically)
            cur.execute("DELETE FROM chatbot_users WHERE id = %s", (user_id,))
            conn.commit()

            logger.info(f"Chatbot user '{username}' (id={user_id}) permanently deleted by {getattr(current_user, 'username', 'unknown')}")
            return {"status": "success", "message": f"Chatbot user '{username}' permanently deleted"}


class BulkDeleteRequest(BaseModel):
    user_ids: List[int]


@router.post("/users/bulk-delete")
async def bulk_delete_chatbot_users(
    request: BulkDeleteRequest,
    current_user: dict = Depends(get_current_user)
):
    """Permanently delete multiple inactive chatbot users in one operation."""
    if not request.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user IDs provided"
        )

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Fetch all requested users
            cur.execute(
                "SELECT id, username, is_active FROM chatbot_users WHERE id = ANY(%s)",
                (request.user_ids,)
            )
            found_users = cur.fetchall()
            found_ids = {u['id'] for u in found_users}

            # Check for missing users
            missing_ids = set(request.user_ids) - found_ids
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Users not found: {list(missing_ids)}"
                )

            # Check for active users
            active_users = [u for u in found_users if u['is_active']]
            if active_users:
                active_names = [u['username'] for u in active_users]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete active users. Deactivate first: {active_names}"
                )

            # Delete all (chatbot_user_groups cascades automatically)
            cur.execute(
                "DELETE FROM chatbot_users WHERE id = ANY(%s)",
                (request.user_ids,)
            )
            conn.commit()

            deleted_names = [u['username'] for u in found_users]
            admin_name = getattr(current_user, 'username', 'unknown')
            logger.info(f"Bulk deleted chatbot users {deleted_names} by {admin_name}")
            return {
                "status": "success",
                "message": f"Permanently deleted {len(deleted_names)} user(s)",
                "deleted_users": deleted_names
            }


@router.post("/users/{user_id}/groups/{group_id}")
async def assign_chatbot_user_to_group(
    user_id: int,
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Assign a chatbot user to a group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chatbot_user_groups (chatbot_user_id, chatbot_group_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (user_id, group_id))
            
            conn.commit()
            return {"status": "success", "message": "User assigned to group"}


@router.delete("/users/{user_id}/groups/{group_id}")
async def remove_chatbot_user_from_group(
    user_id: int,
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Remove a chatbot user from a group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM chatbot_user_groups
                WHERE chatbot_user_id = %s AND chatbot_group_id = %s
            """, (user_id, group_id))
            
            conn.commit()
            return {"status": "success", "message": "User removed from group"}


# ============================================================================
# Chatbot Groups Endpoints
# ============================================================================

@router.get("/groups", response_model=List[ChatbotGroupResponse])
async def get_all_chatbot_groups(current_user: dict = Depends(get_current_user)):
    """Get all chatbot groups with their roles"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cg.id, cg.name, cg.description, cg.is_active, cg.created_at,
                       (SELECT COUNT(*) FROM chatbot_user_groups WHERE chatbot_group_id = cg.id) as user_count
                FROM chatbot_groups cg
                ORDER BY cg.name
            """)
            groups = cur.fetchall()
            
            result = []
            for group in groups:
                # Get roles for each group
                cur.execute("""
                    SELECT cr.id, cr.name, cr.description
                    FROM chatbot_roles cr
                    JOIN chatbot_group_roles cgr ON cr.id = cgr.chatbot_role_id
                    WHERE cgr.chatbot_group_id = %s
                """, (group['id'],))
                roles = [{"id": r['id'], "name": r['name'], "description": r['description']} for r in cur.fetchall()]
                
                result.append({
                    "id": group['id'],
                    "name": group['name'],
                    "description": group['description'],
                    "is_active": group['is_active'],
                    "created_at": group['created_at'],
                    "user_count": group['user_count'],
                    "roles": roles
                })
            
            return result


@router.post("/groups", response_model=ChatbotGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_chatbot_group(
    group_data: ChatbotGroupCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new chatbot group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chatbot_groups (name, description, created_by)
                VALUES (%s, %s, %s)
                RETURNING id, name, description, is_active, created_at
            """, (group_data.name, group_data.description, current_user.id))
            
            group = cur.fetchone()
            conn.commit()
            
            return {
                "id": group['id'],
                "name": group['name'],
                "description": group['description'],
                "is_active": group['is_active'],
                "created_at": group['created_at'],
                "roles": [],
                "user_count": 0
            }


@router.put("/groups/{group_id}", response_model=ChatbotGroupResponse)
async def update_chatbot_group(
    group_id: int,
    group_data: ChatbotGroupUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a chatbot group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            updates = []
            values = []
            
            if group_data.name is not None:
                updates.append("name = %s")
                values.append(group_data.name)
            if group_data.description is not None:
                updates.append("description = %s")
                values.append(group_data.description)
            if group_data.is_active is not None:
                updates.append("is_active = %s")
                values.append(group_data.is_active)
            
            if not updates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(group_id)
            
            query = f"""
                UPDATE chatbot_groups SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, name, description, is_active, created_at
            """
            
            cur.execute(query, values)
            group = cur.fetchone()
            
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chatbot group not found"
                )
            
            # Get roles and user count
            cur.execute("""
                SELECT cr.id, cr.name, cr.description
                FROM chatbot_roles cr
                JOIN chatbot_group_roles cgr ON cr.id = cgr.chatbot_role_id
                WHERE cgr.chatbot_group_id = %s
            """, (group['id'],))
            roles = [{"id": r['id'], "name": r['name'], "description": r['description']} for r in cur.fetchall()]
            
            cur.execute("SELECT COUNT(*) FROM chatbot_user_groups WHERE chatbot_group_id = %s", (group['id'],))
            user_count = cur.fetchone()['count']
            
            conn.commit()
            
            return {
                "id": group['id'],
                "name": group['name'],
                "description": group['description'],
                "is_active": group['is_active'],
                "created_at": group['created_at'],
                "roles": roles,
                "user_count": user_count
            }


@router.delete("/groups/{group_id}")
async def delete_chatbot_group(
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a chatbot group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chatbot_groups WHERE id = %s RETURNING id", (group_id,))
            
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chatbot group not found"
                )
            
            conn.commit()
            return {"status": "success", "message": "Chatbot group deleted"}


@router.post("/groups/{group_id}/roles/{role_id}")
async def assign_role_to_chatbot_group(
    group_id: int,
    role_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Assign a role to a chatbot group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chatbot_group_roles (chatbot_group_id, chatbot_role_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (group_id, role_id))
            
            conn.commit()
            return {"status": "success", "message": "Role assigned to group"}


@router.delete("/groups/{group_id}/roles/{role_id}")
async def remove_role_from_chatbot_group(
    group_id: int,
    role_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Remove a role from a chatbot group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM chatbot_group_roles
                WHERE chatbot_group_id = %s AND chatbot_role_id = %s
            """, (group_id, role_id))
            
            conn.commit()
            return {"status": "success", "message": "Role removed from group"}


# ============================================================================
# Chatbot Roles Endpoints
# ============================================================================

@router.get("/roles", response_model=List[ChatbotRoleResponse])
async def get_all_chatbot_roles(current_user: dict = Depends(get_current_user)):
    """Get all chatbot roles with their permissions"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, description, created_at
                FROM chatbot_roles
                ORDER BY name
            """)
            roles = cur.fetchall()
            
            result = []
            for role in roles:
                # Get permissions for each role
                cur.execute("""
                    SELECT cp.id, cp.name, cp.description, cp.category
                    FROM chatbot_permissions cp
                    JOIN chatbot_role_permissions crp ON cp.id = crp.permission_id
                    WHERE crp.role_id = %s
                """, (role['id'],))
                permissions = [
                    {"id": p['id'], "name": p['name'], "description": p['description'], "category": p['category']}
                    for p in cur.fetchall()
                ]
                
                result.append({
                    "id": role['id'],
                    "name": role['name'],
                    "description": role['description'],
                    "created_at": role['created_at'],
                    "permissions": permissions
                })
            
            return result


@router.post("/roles", response_model=ChatbotRoleResponse, status_code=status.HTTP_201_CREATED)
async def create_chatbot_role(
    role_data: ChatbotRoleCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new chatbot role"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chatbot_roles (name, description, created_by)
                VALUES (%s, %s, %s)
                RETURNING id, name, description, created_at
            """, (role_data.name, role_data.description, current_user.id))
            
            role = cur.fetchone()
            
            # Assign permissions
            permissions = []
            if role_data.permission_ids:
                for perm_id in role_data.permission_ids:
                    cur.execute("""
                        INSERT INTO chatbot_role_permissions (role_id, permission_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (role['id'], perm_id))
                
                cur.execute("""
                    SELECT id, name, description, category
                    FROM chatbot_permissions
                    WHERE id = ANY(%s)
                """, (role_data.permission_ids,))
                permissions = [
                    {"id": p['id'], "name": p['name'], "description": p['description'], "category": p['category']}
                    for p in cur.fetchall()
                ]
            
            conn.commit()
            
            return {
                "id": role['id'],
                "name": role['name'],
                "description": role['description'],
                "created_at": role['created_at'],
                "permissions": permissions
            }


@router.put("/roles/{role_id}", response_model=ChatbotRoleResponse)
async def update_chatbot_role(
    role_id: int,
    role_data: ChatbotRoleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a chatbot role"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            updates = []
            values = []
            
            if role_data.name is not None:
                updates.append("name = %s")
                values.append(role_data.name)
            if role_data.description is not None:
                updates.append("description = %s")
                values.append(role_data.description)
            
            if not updates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(role_id)
            
            query = f"""
                UPDATE chatbot_roles SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, name, description, created_at
            """
            
            cur.execute(query, values)
            role = cur.fetchone()
            
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chatbot role not found"
                )
            
            # Get permissions
            cur.execute("""
                SELECT cp.id, cp.name, cp.description, cp.category
                FROM chatbot_permissions cp
                JOIN chatbot_role_permissions crp ON cp.id = crp.permission_id
                WHERE crp.role_id = %s
            """, (role['id'],))
            permissions = [
                {"id": p['id'], "name": p['name'], "description": p['description'], "category": p['category']}
                for p in cur.fetchall()
            ]
            
            conn.commit()
            
            return {
                "id": role['id'],
                "name": role['name'],
                "description": role['description'],
                "created_at": role['created_at'],
                "permissions": permissions
            }


@router.delete("/roles/{role_id}")
async def delete_chatbot_role(
    role_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a chatbot role"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chatbot_roles WHERE id = %s RETURNING id", (role_id,))
            
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chatbot role not found"
                )
            
            conn.commit()
            return {"status": "success", "message": "Chatbot role deleted"}


@router.post("/roles/{role_id}/permissions/{permission_id}")
async def add_permission_to_role(
    role_id: int,
    permission_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Add a permission to a chatbot role"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chatbot_role_permissions (role_id, permission_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (role_id, permission_id))
            
            conn.commit()
            return {"status": "success", "message": "Permission added to role"}


@router.delete("/roles/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Remove a permission from a chatbot role"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM chatbot_role_permissions
                WHERE role_id = %s AND permission_id = %s
            """, (role_id, permission_id))
            
            conn.commit()
            return {"status": "success", "message": "Permission removed from role"}


# ============================================================================
# Chatbot Permissions Endpoints
# ============================================================================

@router.get("/permissions", response_model=List[ChatbotPermissionResponse])
async def get_all_chatbot_permissions(current_user: dict = Depends(get_current_user)):
    """Get all available chatbot permissions"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, description, category
                FROM chatbot_permissions
                ORDER BY category, name
            """)
            permissions = cur.fetchall()
            
            return [
                {"id": p['id'], "name": p['name'], "description": p['description'], "category": p['category']}
                for p in permissions
            ]


# ============================================================================
# Chatbot Corpus Access Endpoints
# ============================================================================

@router.get("/corpus-access")
async def get_all_corpus_access(current_user: dict = Depends(get_current_user)):
    """Get all corpus access assignments"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cca.id, cca.chatbot_group_id, cg.name as group_name,
                       cca.corpus_id, c.name as corpus_name, c.display_name,
                       cca.permission, cca.granted_at
                FROM chatbot_corpus_access cca
                JOIN chatbot_groups cg ON cca.chatbot_group_id = cg.id
                JOIN corpora c ON cca.corpus_id = c.id
                ORDER BY cg.name, c.name
            """)
            access = cur.fetchall()
            
            return [
                {
                    "id": a['id'],
                    "chatbot_group_id": a['chatbot_group_id'],
                    "group_name": a['group_name'],
                    "corpus_id": a['corpus_id'],
                    "corpus_name": a['corpus_name'],
                    "corpus_display_name": a['display_name'],
                    "permission": a['permission'],
                    "granted_at": a['granted_at']
                }
                for a in access
            ]


@router.post("/corpus-access")
async def grant_corpus_access(
    access_data: ChatbotCorpusAccessCreate,
    current_user: dict = Depends(get_current_user)
):
    """Grant corpus access to a chatbot group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chatbot_corpus_access (chatbot_group_id, corpus_id, permission, granted_by)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (chatbot_group_id, corpus_id) 
                DO UPDATE SET permission = EXCLUDED.permission, granted_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                access_data.chatbot_group_id,
                access_data.corpus_id,
                access_data.permission,
                current_user.id
            ))
            
            conn.commit()
            return {"status": "success", "message": "Corpus access granted"}


@router.delete("/corpus-access/{group_id}/{corpus_id}")
async def revoke_corpus_access(
    group_id: int,
    corpus_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Revoke corpus access from a chatbot group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM chatbot_corpus_access
                WHERE chatbot_group_id = %s AND corpus_id = %s
            """, (group_id, corpus_id))
            
            conn.commit()
            return {"status": "success", "message": "Corpus access revoked"}


# ============================================================================
# Chatbot Agent Access Endpoints
# ============================================================================

@router.get("/agent-access")
async def get_all_agent_access(current_user: dict = Depends(get_current_user)):
    """Get all agent access assignments"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT caa.id, caa.chatbot_group_id, cg.name as group_name,
                       caa.agent_id, a.name as agent_name, a.display_name,
                       caa.can_use, caa.can_configure, caa.granted_at
                FROM chatbot_agent_access caa
                JOIN chatbot_groups cg ON caa.chatbot_group_id = cg.id
                JOIN agents a ON caa.agent_id = a.id
                ORDER BY cg.name, a.name
            """)
            access = cur.fetchall()
            
            return [
                {
                    "id": a['id'],
                    "chatbot_group_id": a['chatbot_group_id'],
                    "group_name": a['group_name'],
                    "agent_id": a['agent_id'],
                    "agent_name": a['agent_name'],
                    "agent_display_name": a['display_name'],
                    "can_use": a['can_use'],
                    "can_configure": a['can_configure'],
                    "granted_at": a['granted_at']
                }
                for a in access
            ]


@router.post("/agent-access")
async def grant_agent_access(
    access_data: ChatbotAgentAccessCreate,
    current_user: dict = Depends(get_current_user)
):
    """Grant agent access to a chatbot group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chatbot_agent_access (chatbot_group_id, agent_id, can_use, can_configure, granted_by)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (chatbot_group_id, agent_id) 
                DO UPDATE SET can_use = EXCLUDED.can_use, can_configure = EXCLUDED.can_configure, granted_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                access_data.chatbot_group_id,
                access_data.agent_id,
                access_data.can_use,
                access_data.can_configure,
                current_user.id
            ))
            
            conn.commit()
            return {"status": "success", "message": "Agent access granted"}


@router.delete("/agent-access/{group_id}/{agent_id}")
async def revoke_agent_access(
    group_id: int,
    agent_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Revoke agent access from a chatbot group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM chatbot_agent_access
                WHERE chatbot_group_id = %s AND agent_id = %s
            """, (group_id, agent_id))
            
            conn.commit()
            return {"status": "success", "message": "Agent access revoked"}


# ============================================================================
# Available Resources Endpoints (for dropdowns)
# ============================================================================

@router.get("/available-corpora")
async def get_available_corpora(current_user: dict = Depends(get_current_user)):
    """Get all available corpora for assignment"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.name, c.display_name, c.description, c.is_active,
                       COALESCE(cm.document_count, 0) as document_count
                FROM corpora c
                LEFT JOIN corpus_metadata cm ON c.id = cm.corpus_id
                WHERE c.is_active = TRUE
                ORDER BY c.name
            """)
            corpora = cur.fetchall()
            
            return [
                {
                    "id": c['id'],
                    "name": c['name'],
                    "display_name": c['display_name'],
                    "description": c['description'],
                    "is_active": c['is_active'],
                    "document_count": c['document_count']
                }
                for c in corpora
            ]


@router.get("/available-agents")
async def get_available_agents(current_user: dict = Depends(get_current_user)):
    """Get all available agents for assignment"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, display_name, description, is_active
                FROM agents
                WHERE is_active = TRUE
                ORDER BY name
            """)
            agents = cur.fetchall()
            
            return [
                {
                    "id": a['id'],
                    "name": a['name'],
                    "display_name": a['display_name'],
                    "description": a['description'],
                    "is_active": a['is_active']
                }
                for a in agents
            ]


# ============================================================================
# Agent Type Hierarchy Endpoints
# ============================================================================

@router.get("/agent-type-hierarchy")
async def get_agent_type_hierarchy(current_user: dict = Depends(get_current_user)):
    """
    Get the agent type hierarchy with tool definitions.
    
    Returns information about all agent types in hierarchical order:
    - Viewer → Contributor → Content Manager → Corpus Manager
    
    Each agent type includes:
    - type: The agent type identifier
    - display_name: Human-readable name
    - description: Brief description
    - use_case: Explanation of when to use this type
    - color: UI color scheme
    - tools: All tools available (including inherited)
    - incremental_tools: Tools added by this type only
    """
    return get_agent_type_hierarchy_list()


@router.get("/agent-type-tools/{agent_type}")
async def get_agent_type_tools(agent_type: str, current_user: dict = Depends(get_current_user)):
    """
    Get all tools available to a specific agent type.
    
    Args:
        agent_type: One of 'viewer', 'contributor', 'content-manager', 'corpus-manager'
        
    Returns:
        List of tool names available to this agent type (including inherited tools)
    """
    if not validate_agent_type(agent_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent type: {agent_type}. Must be one of: viewer, contributor, content-manager, corpus-manager"
        )
    
    agent_type_enum = AgentType(agent_type)
    tools = get_all_tools_for_agent_type(agent_type_enum)
    
    return {
        "agent_type": agent_type,
        "tools": tools,
        "tool_count": len(tools)
    }


@router.get("/my-agent-type")
async def get_my_agent_type(current_user: dict = Depends(get_current_user)):
    """
    Get the current user's agent type and allowed tools.
    
    Returns information about the user's assigned agent type through their chatbot groups.
    If user belongs to multiple groups with different agent types, returns the highest level.
    
    Returns:
        - agent_type: The user's agent type (or null if none assigned)
        - allowed_tools: List of tools the user can access
        - tool_count: Number of tools available
    """
    user_agent_type = await get_user_agent_type(current_user)
    allowed_tools = await get_user_allowed_tools(current_user)
    
    return {
        "agent_type": user_agent_type,
        "allowed_tools": allowed_tools,
        "tool_count": len(allowed_tools)
    }


# ============================================================================
# Chatbot Agents Endpoints
# ============================================================================

@router.get("/agents", response_model=List[ChatbotAgentResponse])
async def get_all_chatbot_agents(current_user: dict = Depends(get_current_user)):
    """Get all chatbot agents with their tool configurations"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, display_name, description, agent_type, tools, is_active, created_at
                FROM chatbot_agents
                ORDER BY id
            """)
            agents = cur.fetchall()
            
            return [
                {
                    "id": a['id'],
                    "name": a['name'],
                    "display_name": a['display_name'],
                    "description": a['description'],
                    "agent_type": a['agent_type'],
                    "tools": a['tools'],
                    "is_active": a['is_active'],
                    "created_at": a['created_at']
                }
                for a in agents
            ]


@router.get("/agents/{agent_id}", response_model=ChatbotAgentResponse)
async def get_chatbot_agent(agent_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific chatbot agent by ID"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, display_name, description, agent_type, tools, is_active, created_at
                FROM chatbot_agents
                WHERE id = %s
            """, (agent_id,))
            agent = cur.fetchone()
            
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            return {
                "id": agent['id'],
                "name": agent['name'],
                "display_name": agent['display_name'],
                "description": agent['description'],
                "agent_type": agent['agent_type'],
                "tools": agent['tools'],
                "is_active": agent['is_active'],
                "created_at": agent['created_at']
            }


@router.get("/me/available-agents")
async def get_my_available_agents(current_user = Depends(get_current_user)):
    """Get all agents available to the current logged-in chatbot user"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # First, get the chatbot_user_id from the app user (via user_id FK)
            cur.execute("""
                SELECT id FROM chatbot_users WHERE user_id = %s
            """, (current_user.id,))
            chatbot_user = cur.fetchone()
            
            if not chatbot_user:
                return []
            
            # Get agents available through user's groups
            cur.execute("""
                SELECT DISTINCT a.id, a.name, a.display_name, a.description, 
                       a.agent_type, a.tools, a.is_active, a.created_at
                FROM chatbot_agents a
                JOIN chatbot_group_agents ga ON a.id = ga.agent_id
                JOIN chatbot_user_groups ug ON ga.group_id = ug.chatbot_group_id
                WHERE ug.chatbot_user_id = %s 
                  AND a.is_active = TRUE 
                  AND ga.can_use = TRUE
                ORDER BY a.id
            """, (chatbot_user['id'],))
            agents = cur.fetchall()
            
            return [
                {
                    "id": a['id'],
                    "name": a['name'],
                    "display_name": a['display_name'],
                    "description": a['description'],
                    "agent_type": a['agent_type'],
                    "tools": a['tools'],
                    "is_active": a['is_active'],
                    "created_at": a['created_at']
                }
                for a in agents
            ]


@router.get("/users/{user_id}/available-agents")
async def get_user_available_agents(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get all agents available to a specific user based on their group memberships"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get agents available through user's groups
            cur.execute("""
                SELECT DISTINCT a.id, a.name, a.display_name, a.description, 
                       a.agent_type, a.tools, a.is_active, a.created_at
                FROM chatbot_agents a
                JOIN chatbot_group_agents ga ON a.id = ga.agent_id
                JOIN chatbot_user_groups ug ON ga.group_id = ug.chatbot_group_id
                WHERE ug.chatbot_user_id = %s 
                  AND a.is_active = TRUE 
                  AND ga.can_use = TRUE
                ORDER BY a.id
            """, (user_id,))
            agents = cur.fetchall()
            
            return [
                {
                    "id": a['id'],
                    "name": a['name'],
                    "display_name": a['display_name'],
                    "description": a['description'],
                    "agent_type": a['agent_type'],
                    "tools": a['tools'],
                    "is_active": a['is_active'],
                    "created_at": a['created_at']
                }
                for a in agents
            ]


@router.get("/groups/{group_id}/agents")
async def get_group_agents(group_id: int, current_user: dict = Depends(get_current_user)):
    """Get all agents assigned to a specific group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, a.name, a.display_name, a.description, 
                       a.agent_type, a.tools, a.is_active, a.created_at,
                       ga.can_use, ga.granted_at
                FROM chatbot_agents a
                JOIN chatbot_group_agents ga ON a.id = ga.agent_id
                WHERE ga.group_id = %s
                ORDER BY a.id
            """, (group_id,))
            agents = cur.fetchall()
            
            return [
                {
                    "id": a['id'],
                    "name": a['name'],
                    "display_name": a['display_name'],
                    "description": a['description'],
                    "agent_type": a['agent_type'],
                    "tools": a['tools'],
                    "is_active": a['is_active'],
                    "created_at": a['created_at'],
                    "can_use": a['can_use'],
                    "granted_at": a['granted_at']
                }
                for a in agents
            ]


@router.post("/groups/{group_id}/agents/{agent_id}")
async def assign_agent_to_group(
    group_id: int, 
    agent_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Assign an agent to a group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check if group exists
            cur.execute("SELECT id FROM chatbot_groups WHERE id = %s", (group_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Group not found")
            
            # Check if agent exists
            cur.execute("SELECT id FROM chatbot_agents WHERE id = %s", (agent_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Agent not found")
            
            # Assign agent to group
            try:
                cur.execute("""
                    INSERT INTO chatbot_group_agents (group_id, agent_id, can_use, granted_by)
                    VALUES (%s, %s, TRUE, %s)
                    ON CONFLICT (group_id, agent_id) 
                    DO UPDATE SET can_use = TRUE
                """, (group_id, agent_id, current_user.id if hasattr(current_user, 'id') else current_user['id']))
                conn.commit()
                
                return {"message": "Agent assigned to group successfully"}
            except Exception as e:
                logger.error(f"Error assigning agent to group: {e}")
                raise HTTPException(status_code=500, detail=str(e))


@router.delete("/groups/{group_id}/agents/{agent_id}")
async def remove_agent_from_group(
    group_id: int,
    agent_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Remove an agent from a group"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM chatbot_group_agents
                WHERE group_id = %s AND agent_id = %s
            """, (group_id, agent_id))
            conn.commit()
            
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Agent assignment not found")
            
            return {"message": "Agent removed from group successfully"}
