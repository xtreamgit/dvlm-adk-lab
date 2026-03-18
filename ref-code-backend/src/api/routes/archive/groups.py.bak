"""
Group and role management routes (admin only).
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends

from services.group_service import GroupService
from services.user_service import UserService
from models.group import Group, GroupCreate, GroupUpdate, Role, RoleCreate
from models.user import User
from middleware.iap_auth_middleware import get_current_user_iap as get_current_user
from fastapi import HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/groups", tags=["Groups & Roles"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin privileges."""
    from services.user_service import UserService
    from database.repositories import GroupRepository
    
    user_group_ids = UserService.get_user_groups(current_user.id)
    user_groups = [GroupRepository.get_group_by_id(gid) for gid in user_group_ids]
    user_groups = [g for g in user_groups if g is not None]
    is_admin = any(group['name'] == 'admin-users' for group in user_groups)
    
    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    
    return current_user


# ========== Group Endpoints ==========

@router.get("/me", response_model=List[Group])
async def get_my_groups(current_user: User = Depends(get_current_user)):
    """
    Get current user's groups.
    """
    group_ids = UserService.get_user_groups(current_user.id)
    groups = []
    
    for group_id in group_ids:
        group = GroupService.get_group_by_id(group_id)
        if group:
            groups.append(group)
    
    return groups


@router.get("/", response_model=List[Group])
async def list_groups(
    current_user: User = Depends(require_admin)
):
    """
    List all groups (admin only).
    
    Requires 'manage:groups' permission.
    """
    return GroupService.get_all_groups()


@router.get("/{group_id}", response_model=Group)
async def get_group(
    group_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Get group details (admin only).
    
    Requires 'manage:groups' permission.
    """
    group = GroupService.get_group_by_id(group_id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    return group


@router.post("/", response_model=Group, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_create: GroupCreate,
    current_user: User = Depends(require_admin)
):
    """
    Create a new group (admin only).
    
    Requires 'manage:groups' permission.
    """
    try:
        group = GroupService.create_group(group_create)
        logger.info(f"Group created by {current_user.username}: {group.name}")
        return group
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{group_id}", response_model=Group)
async def update_group(
    group_id: int,
    group_update: GroupUpdate,
    current_user: User = Depends(require_admin)
):
    """
    Update group (admin only).
    
    Requires 'manage:groups' permission.
    """
    updated_group = GroupService.update_group(group_id, group_update)
    
    if not updated_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    logger.info(f"Group updated by {current_user.username}: {updated_group.name}")
    return updated_group


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Delete a group (admin only).
    
    Requires 'manage:groups' permission.
    """
    # Verify group exists
    group = GroupService.get_group_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    success = GroupService.delete_group(group_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete group"
        )
    
    logger.info(f"Group {group.name} deleted by {current_user.username}")
    return {"message": "Group deleted successfully"}


@router.get("/{group_id}/users")
async def get_group_users(
    group_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Get all users in a group (admin only).
    
    Requires 'manage:groups' permission.
    """
    # Verify group exists
    group = GroupService.get_group_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    users = GroupService.get_group_users(group_id)
    return users


@router.put("/{group_id}/users/{user_id}")
async def add_user_to_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Add user to a group (admin only).
    
    Requires 'manage:groups' permission.
    """
    # Verify group exists
    group = GroupService.get_group_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Verify user exists
    user = UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = UserService.add_user_to_group(user_id, group_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add user to group (may already be member)"
        )
    
    logger.info(f"User {user.username} added to group {group.name} by {current_user.username}")
    return {"message": "User added to group successfully"}


@router.delete("/{group_id}/users/{user_id}")
async def remove_user_from_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Remove user from a group (admin only).
    
    Requires 'manage:groups' permission.
    """
    success = UserService.remove_user_from_group(user_id, group_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or group not found, or user not in group"
        )
    
    logger.info(f"User {user_id} removed from group {group_id} by {current_user.username}")
    return {"message": "User removed from group successfully"}


# ========== Role Endpoints ==========

@router.get("/roles/", response_model=List[Role])
async def list_roles(
    current_user: User = Depends(require_admin)
):
    """
    List all roles (admin only).
    
    Requires 'manage:roles' permission.
    """
    return GroupService.get_all_roles()


@router.get("/roles/{role_id}", response_model=Role)
async def get_role(
    role_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Get role details (admin only).
    
    Requires 'manage:roles' permission.
    """
    role = GroupService.get_role_by_id(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    return role


@router.post("/roles/", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_create: RoleCreate,
    current_user: User = Depends(require_admin)
):
    """
    Create a new role (admin only).
    
    Requires 'manage:roles' permission.
    """
    try:
        role = GroupService.create_role(role_create)
        logger.info(f"Role created by {current_user.username}: {role.name}")
        return role
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{group_id}/roles/{role_id}")
async def assign_role_to_group(
    group_id: int,
    role_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Assign role to a group (admin only).
    
    Requires 'manage:roles' permission.
    """
    # Verify group exists
    group = GroupService.get_group_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Verify role exists
    role = GroupService.get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    success = GroupService.assign_role_to_group(group_id, role_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign role to group (may already be assigned)"
        )
    
    logger.info(f"Role {role.name} assigned to group {group.name} by {current_user.username}")
    return {"message": "Role assigned to group successfully"}


@router.delete("/{group_id}/roles/{role_id}")
async def remove_role_from_group(
    group_id: int,
    role_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Remove role from a group (admin only).
    
    Requires 'manage:roles' permission.
    """
    success = GroupService.remove_role_from_group(group_id, role_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group or role not found, or role not assigned to group"
        )
    
    logger.info(f"Role {role_id} removed from group {group_id} by {current_user.username}")
    return {"message": "Role removed from group successfully"}


@router.get("/{group_id}/roles", response_model=List[Role])
async def get_group_roles(
    group_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get roles for a specific group.
    """
    # Verify group exists
    group = GroupService.get_group_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    return GroupService.get_group_roles(group_id)
