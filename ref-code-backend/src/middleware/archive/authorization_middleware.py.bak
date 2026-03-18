"""
Authorization middleware for role-based access control.
"""

import logging
from typing import Callable

from fastapi import Depends, HTTPException, status

from services.group_service import GroupService
from models.user import User
from middleware.iap_auth_middleware import get_current_user_iap as get_current_user

logger = logging.getLogger(__name__)


def require_permission(permission: str) -> Callable:
    """
    Decorator factory to require a specific permission for an endpoint.
    
    Usage:
        @app.get("/admin/users")
        async def get_users(user: User = Depends(require_permission("manage:users"))):
            ...
    
    Args:
        permission: Permission string required (e.g., "read:corpus", "manage:users")
        
    Returns:
        FastAPI dependency function
    """
    async def permission_checker(user: User = Depends(get_current_user)) -> User:
        """Check if user has required permission."""
        has_permission = GroupService.check_permission(user.id, permission)
        
        if not has_permission:
            logger.warning(
                f"User {user.username} (ID: {user.id}) denied access. "
                f"Required permission: {permission}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        
        return user
    
    return permission_checker


def require_any_permission(*permissions: str) -> Callable:
    """
    Decorator factory to require ANY of the specified permissions.
    
    Usage:
        @app.get("/resources")
        async def get_resources(
            user: User = Depends(require_any_permission("read:corpus", "write:corpus"))
        ):
            ...
    
    Args:
        *permissions: Variable number of permission strings
        
    Returns:
        FastAPI dependency function
    """
    async def permission_checker(user: User = Depends(get_current_user)) -> User:
        """Check if user has any of the required permissions."""
        for permission in permissions:
            if GroupService.check_permission(user.id, permission):
                return user
        
        logger.warning(
            f"User {user.username} (ID: {user.id}) denied access. "
            f"Required any of: {', '.join(permissions)}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required any of: {', '.join(permissions)}"
        )
    
    return permission_checker


def require_all_permissions(*permissions: str) -> Callable:
    """
    Decorator factory to require ALL of the specified permissions.
    
    Usage:
        @app.post("/admin/corpus")
        async def create_corpus(
            user: User = Depends(require_all_permissions("create:corpus", "manage:corpora"))
        ):
            ...
    
    Args:
        *permissions: Variable number of permission strings
        
    Returns:
        FastAPI dependency function
    """
    async def permission_checker(user: User = Depends(get_current_user)) -> User:
        """Check if user has all of the required permissions."""
        for permission in permissions:
            if not GroupService.check_permission(user.id, permission):
                logger.warning(
                    f"User {user.username} (ID: {user.id}) denied access. "
                    f"Missing permission: {permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Missing: {permission}"
                )
        
        return user
    
    return permission_checker
