"""
Agent management routes: list agents, switch agents, manage access.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends

from services.agent_service import AgentService
from services.session_service import SessionService
from models.agent import Agent, AgentCreate, AgentWithAccess
from models.user import User
from middleware.iap_auth_middleware import get_current_user_iap as get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.get("/", response_model=List[Agent])
async def list_all_agents(current_user: User = Depends(get_current_user)):
    """
    List all available agents.
    
    Returns all active agents in the system.
    """
    return AgentService.get_all_agents(active_only=True)


@router.get("/me", response_model=List[AgentWithAccess])
async def get_my_agents(current_user: User = Depends(get_current_user)):
    """
    Get agents current user has access to.
    
    Returns list of agents with access information and default agent indicator.
    """
    return AgentService.get_user_agents(current_user.id, active_only=True)


@router.get("/default", response_model=Agent)
async def get_default_agent(current_user: User = Depends(get_current_user)):
    """
    Get user's default agent.
    """
    agent = AgentService.get_default_agent(current_user.id)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default agent set"
        )
    
    return agent


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get agent details by ID.
    """
    agent = AgentService.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return agent


@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_create: AgentCreate,
    current_user: User = Depends(get_current_user)  # TODO: Add Google Groups admin check
):
    """
    Create a new agent (admin only).
    
    Requires 'manage:agents' permission.
    """
    try:
        agent = AgentService.create_agent(agent_create)
        logger.info(f"Agent created by {current_user.email}: {agent.name}")
        return agent
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{agent_id}/activate")
async def activate_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user)  # TODO: Add Google Groups admin check
):
    """
    Activate an agent (admin only).
    
    Requires 'manage:agents' permission.
    """
    agent = AgentService.update_agent(agent_id, is_active=True)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    logger.info(f"Agent {agent.name} activated by {current_user.email}")
    return {"message": "Agent activated successfully"}


@router.put("/{agent_id}/deactivate")
async def deactivate_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user)  # TODO: Add Google Groups admin check
):
    """
    Deactivate an agent (admin only).
    
    Requires 'manage:agents' permission.
    """
    agent = AgentService.update_agent(agent_id, is_active=False)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    logger.info(f"Agent {agent.name} deactivated by {current_user.email}")
    return {"message": "Agent deactivated successfully"}


# ========== User-Agent Access Management ==========

@router.put("/{agent_id}/grant/{user_id}")
async def grant_agent_access(
    agent_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user)  # TODO: Add Google Groups admin check
):
    """
    Grant user access to an agent (admin only).
    
    Requires 'manage:agent_access' permission.
    """
    # Verify agent exists
    agent = AgentService.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify user exists
    from ...services import UserService
    user = UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = AgentService.grant_user_access(user_id, agent_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to grant access (may already have access)"
        )
    
    logger.info(f"User {user_id} granted access to agent {agent.name} by {current_user.email}")
    return {"message": "Access granted successfully"}


@router.delete("/{agent_id}/revoke/{user_id}")
async def revoke_agent_access(
    agent_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user)  # TODO: Add Google Groups admin check
):
    """
    Revoke user access to an agent (admin only).
    
    Requires 'manage:agent_access' permission.
    """
    success = AgentService.revoke_user_access(user_id, agent_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access not found or already revoked"
        )
    
    logger.info(f"User {user_id} access revoked for agent {agent_id} by {current_user.email}")
    return {"message": "Access revoked successfully"}


# ========== Session Agent Switching ==========

@router.post("/sessions/{session_id}/switch/{agent_id}")
async def switch_session_agent(
    session_id: str,
    agent_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Switch active agent for a session.
    
    - **session_id**: Session ID
    - **agent_id**: Agent ID to switch to
    
    User must have access to the agent.
    """
    # Verify user has access to the agent
    if not AgentService.validate_agent_access(current_user.id, agent_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this agent"
        )
    
    # Verify agent exists and is active
    agent = AgentService.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent is not active"
        )
    
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
    
    # Switch agent
    success = SessionService.switch_agent(session_id, agent_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to switch agent"
        )
    
    logger.info(f"User {current_user.email} switched session {session_id} to agent {agent.name}")
    
    return {
        "message": "Agent switched successfully",
        "session_id": session_id,
        "agent": agent
    }
