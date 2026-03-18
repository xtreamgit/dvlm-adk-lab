"""
Tool Permission Middleware

Validates that users have the appropriate agent type to access specific tools.
Enforces the agent type hierarchy for tool access control.
"""

from fastapi import HTTPException, status, Depends
from typing import Optional
import logging

from middleware.iap_auth_middleware import get_current_user_iap as get_current_user
from database.connection import get_db_connection
from services.agent_hierarchy import (
    can_agent_type_use_tool,
    AgentType,
    validate_agent_type,
    get_minimum_agent_type_for_tool
)

logger = logging.getLogger(__name__)


async def get_user_agent_type(current_user: dict = Depends(get_current_user)) -> Optional[str]:
    """
    Get the agent type assigned to the current user through their chatbot groups.
    
    If a user belongs to multiple groups with different agent types,
    returns the highest level (most permissive) agent type.
    
    Links users to chatbot_users via the user_id FK column.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Agent type string or None if no agent type assigned or user not in chatbot_users
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get all agent types assigned to user's groups
            # chatbot_users is linked to users via user_id FK
            cur.execute("""
                SELECT cat.name as agent_type,
                    CASE cat.name
                        WHEN 'admin' THEN 4
                        WHEN 'content-manager' THEN 3
                        WHEN 'contributor' THEN 2
                        WHEN 'viewer' THEN 1
                        ELSE 0
                    END as priority
                FROM chatbot_users cu
                JOIN chatbot_user_groups cug ON cu.id = cug.chatbot_user_id
                JOIN chatbot_group_roles cgat ON cug.chatbot_group_id = cgat.chatbot_group_id
                JOIN chatbot_roles cat ON cgat.chatbot_role_id = cat.id
                WHERE cu.user_id = %s
                ORDER BY priority DESC
                LIMIT 1
            """, (current_user.id,))
            
            result = cur.fetchone()
            return result['agent_type'] if result else None


async def validate_tool_access(
    tool_name: str,
    current_user: dict = Depends(get_current_user)
) -> bool:
    """
    Validate that the current user has access to a specific tool.
    
    Args:
        tool_name: Name of the tool to check access for
        current_user: Current authenticated user
        
    Returns:
        True if user has access, raises HTTPException otherwise
        
    Raises:
        HTTPException: If user doesn't have access to the tool
    """
    user_agent_type = await get_user_agent_type(current_user)
    
    if not user_agent_type:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No agent type assigned. Please contact an administrator to assign you to a chatbot group with an agent type."
        )
    
    if not validate_agent_type(user_agent_type):
        logger.error(f"Invalid agent type in database: {user_agent_type}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid agent type configuration. Please contact an administrator."
        )
    
    agent_type_enum = AgentType(user_agent_type)
    
    if not can_agent_type_use_tool(agent_type_enum, tool_name):
        minimum_type = get_minimum_agent_type_for_tool(tool_name)
        minimum_type_name = minimum_type.value if minimum_type else "unknown"
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Tool '{tool_name}' requires at least '{minimum_type_name}' agent type. Your agent type: '{user_agent_type}'"
        )
    
    return True


def require_tool_access(tool_name: str):
    """
    Dependency factory for requiring specific tool access.
    
    Usage:
        @router.post("/some-endpoint")
        async def endpoint(
            _: bool = Depends(require_tool_access("rag_query")),
            current_user: dict = Depends(get_current_user)
        ):
            # Endpoint logic here
            pass
    
    Args:
        tool_name: Name of the tool required
        
    Returns:
        Dependency function that validates tool access
    """
    async def dependency(current_user: dict = Depends(get_current_user)) -> bool:
        return await validate_tool_access(tool_name, current_user)
    
    return dependency


def require_agent_type(minimum_agent_type: AgentType):
    """
    Dependency factory for requiring a minimum agent type level.
    
    Usage:
        @router.post("/some-endpoint")
        async def endpoint(
            _: bool = Depends(require_agent_type(AgentType.CONTRIBUTOR)),
            current_user: dict = Depends(get_current_user)
        ):
            # Endpoint logic here
            pass
    
    Args:
        minimum_agent_type: Minimum agent type required
        
    Returns:
        Dependency function that validates agent type level
    """
    async def dependency(current_user: dict = Depends(get_current_user)) -> bool:
        user_agent_type = await get_user_agent_type(current_user)
        
        if not user_agent_type:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No agent type assigned. Please contact an administrator."
            )
        
        if not validate_agent_type(user_agent_type):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid agent type configuration."
            )
        
        user_agent_type_enum = AgentType(user_agent_type)
        
        # Check if user's agent type is at or above the minimum required level
        agent_type_levels = {
            AgentType.VIEWER: 1,
            AgentType.CONTRIBUTOR: 2,
            AgentType.CONTENT_MANAGER: 3,
            AgentType.CORPUS_MANAGER: 4,
        }
        
        user_level = agent_type_levels.get(user_agent_type_enum, 0)
        required_level = agent_type_levels.get(minimum_agent_type, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires at least '{minimum_agent_type.value}' agent type. Your agent type: '{user_agent_type}'"
            )
        
        return True
    
    return dependency


async def get_user_allowed_tools(current_user: dict = Depends(get_current_user)) -> list[str]:
    """
    Get list of all tools the current user is allowed to access.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of tool names the user can access
    """
    from services.agent_hierarchy import get_all_tools_for_agent_type
    
    user_agent_type = await get_user_agent_type(current_user)
    
    if not user_agent_type:
        return []
    
    if not validate_agent_type(user_agent_type):
        return []
    
    agent_type_enum = AgentType(user_agent_type)
    return get_all_tools_for_agent_type(agent_type_enum)
