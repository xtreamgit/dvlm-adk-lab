"""
User management routes: profile, preferences, default agent.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends

from services.user_service import UserService
from services.agent_service import AgentService
from models.user import User, UserUpdate, UserProfile, UserProfileUpdate, UserWithProfile
from middleware.iap_auth_middleware import get_current_user_iap as get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserWithProfile)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile with preferences.
    """
    profile = UserService.get_user_profile(current_user.id)
    
    return UserWithProfile(
        **current_user.model_dump(),
        profile=profile
    )


@router.put("/me", response_model=User)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's information.
    
    - **email**: New email address (optional)
    - **full_name**: New full name (optional)
    - **default_agent_id**: Set default agent (optional)
    """
    try:
        updated_user = UserService.update_user(current_user.id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User profile updated: {current_user.email}")
        return updated_user
        
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.get("/me/preferences", response_model=UserProfile)
async def get_my_preferences(current_user: User = Depends(get_current_user)):
    """
    Get current user's preferences.
    """
    profile = UserService.get_user_profile(current_user.id)
    
    if not profile:
        # Create default profile if doesn't exist
        from ...database.repositories import UserRepository
        UserRepository.create_profile(current_user.id)
        profile = UserService.get_user_profile(current_user.id)
    
    return profile


@router.put("/me/preferences", response_model=UserProfile)
async def update_my_preferences(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's preferences.
    
    - **theme**: UI theme ('light' or 'dark')
    - **language**: Language code (e.g., 'en', 'es')
    - **timezone**: Timezone (e.g., 'UTC', 'America/New_York')
    - **preferences**: Custom preferences object
    """
    try:
        updated_profile = UserService.update_user_profile(current_user.id, profile_update)
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        logger.info(f"User preferences updated: {current_user.email}")
        return updated_profile
        
    except Exception as e:
        logger.error(f"Preferences update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Preferences update failed"
        )


@router.put("/me/default-agent/{agent_id}", response_model=User)
async def set_default_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Set user's default agent.
    
    - **agent_id**: ID of the agent to set as default
    
    User must have access to the agent.
    """
    # Validate user has access to the agent
    if not AgentService.validate_agent_access(current_user.id, agent_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this agent"
        )
    
    # Check agent exists
    agent = AgentService.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    success = UserService.set_default_agent(current_user.id, agent_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set default agent"
        )
    
    updated_user = UserService.get_user_by_id(current_user.id)
    logger.info(f"User {current_user.email} set default agent to {agent.name}")
    
    return updated_user


@router.get("/me/groups", response_model=List[int])
async def get_my_groups(current_user: User = Depends(get_current_user)):
    """
    Get current user's group memberships (group IDs).
    """
    return UserService.get_user_groups(current_user.id)


@router.get("/me/roles")
async def get_my_roles(current_user: User = Depends(get_current_user)):
    """
    Get current user's roles (through group memberships).
    
    Deprecated: Legacy roles table has been removed.
    Role-based access is now managed via Google Groups Bridge → chatbot_groups.
    """
    return []
