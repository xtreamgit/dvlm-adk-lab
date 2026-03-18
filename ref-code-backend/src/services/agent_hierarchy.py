"""
Agent Type Hierarchy and Tool Management

Defines the hierarchical relationship between agent types and their associated tools.
Each agent type inherits tools from its parent type.

Hierarchy:
    Viewer → Contributor → Content Manager → Admin
"""

from typing import List, Dict, Set
from enum import Enum


class AgentType(str, Enum):
    """Agent type enumeration matching the hierarchy"""
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    CONTENT_MANAGER = "content-manager"
    ADMIN = "admin"


# Tool definitions for each agent type (incremental)
AGENT_TYPE_TOOLS: Dict[AgentType, List[str]] = {
    AgentType.VIEWER: [
        "rag_query",
        "list_corpora",
        "get_corpus_info",
        "browse_documents",
        "set_current_corpus",
    ],
    AgentType.CONTRIBUTOR: [
        "add_data",
    ],
    AgentType.CONTENT_MANAGER: [
        "delete_document",
    ],
    AgentType.ADMIN: [
        "create_corpus",
        "delete_corpus",
        "rag_multi_query",
        "retrieve_document",
    ],
}


# Agent type hierarchy (parent relationships)
AGENT_TYPE_HIERARCHY: Dict[AgentType, AgentType | None] = {
    AgentType.VIEWER: None,  # Base type, no parent
    AgentType.CONTRIBUTOR: AgentType.VIEWER,
    AgentType.CONTENT_MANAGER: AgentType.CONTRIBUTOR,
    AgentType.ADMIN: AgentType.CONTENT_MANAGER,
}


def get_all_tools_for_agent_type(agent_type: AgentType) -> List[str]:
    """
    Get all tools available to an agent type, including inherited tools.
    
    Args:
        agent_type: The agent type to get tools for
        
    Returns:
        List of tool names available to this agent type
        
    Example:
        >>> get_all_tools_for_agent_type(AgentType.CONTRIBUTOR)
        ['rag_query', 'list_corpora', 'get_corpus_info', 'browse_documents', 'add_data']
    """
    tools: Set[str] = set()
    current_type = agent_type
    
    # Traverse up the hierarchy collecting tools
    while current_type is not None:
        tools.update(AGENT_TYPE_TOOLS.get(current_type, []))
        current_type = AGENT_TYPE_HIERARCHY.get(current_type)
    
    return sorted(list(tools))


def get_incremental_tools_for_agent_type(agent_type: AgentType) -> List[str]:
    """
    Get only the tools added by this specific agent type (not inherited).
    
    Args:
        agent_type: The agent type to get incremental tools for
        
    Returns:
        List of tool names added by this agent type only
    """
    return AGENT_TYPE_TOOLS.get(agent_type, [])


def validate_agent_type(agent_type_str: str) -> bool:
    """
    Validate if a string is a valid agent type.
    
    Args:
        agent_type_str: String to validate
        
    Returns:
        True if valid agent type, False otherwise
    """
    try:
        AgentType(agent_type_str)
        return True
    except ValueError:
        return False


def get_agent_type_display_info(agent_type: AgentType) -> Dict[str, any]:
    """
    Get display information for an agent type.
    
    Args:
        agent_type: The agent type to get info for
        
    Returns:
        Dictionary with display_name, description, color, and tools
    """
    info_map = {
        AgentType.VIEWER: {
            "display_name": "Viewer Agent",
            "description": "Read-only access for general users",
            "color": "blue",
            "use_case": "Minimum viable toolset for querying and viewing information",
        },
        AgentType.CONTRIBUTOR: {
            "display_name": "Contributor Agent",
            "description": "Users who can add content",
            "color": "emerald",
            "use_case": "All viewer tools + ability to add documents",
        },
        AgentType.CONTENT_MANAGER: {
            "display_name": "Content Manager Agent",
            "description": "Manage documents within existing corpora",
            "color": "amber",
            "use_case": "Contributor tools + document deletion",
        },
        AgentType.ADMIN: {
            "display_name": "Admin Agent",
            "description": "Full corpus lifecycle management",
            "color": "purple",
            "use_case": "ALL TOOLS - Complete control over corpora and documents",
        },
    }
    
    info = info_map.get(agent_type, {})
    info["tools"] = get_all_tools_for_agent_type(agent_type)
    info["incremental_tools"] = get_incremental_tools_for_agent_type(agent_type)
    
    return info


def can_agent_type_use_tool(agent_type: AgentType, tool_name: str) -> bool:
    """
    Check if an agent type has access to a specific tool.
    
    Args:
        agent_type: The agent type to check
        tool_name: The tool name to check access for
        
    Returns:
        True if agent type can use the tool, False otherwise
    """
    allowed_tools = get_all_tools_for_agent_type(agent_type)
    return tool_name in allowed_tools


def get_minimum_agent_type_for_tool(tool_name: str) -> AgentType | None:
    """
    Get the minimum (lowest level) agent type that has access to a tool.
    
    Args:
        tool_name: The tool name to check
        
    Returns:
        The minimum agent type that can use this tool, or None if tool not found
    """
    # Check in order from lowest to highest
    for agent_type in [AgentType.VIEWER, AgentType.CONTRIBUTOR, 
                       AgentType.CONTENT_MANAGER, AgentType.ADMIN]:
        if tool_name in get_all_tools_for_agent_type(agent_type):
            return agent_type
    
    return None


def get_agent_type_hierarchy_list() -> List[Dict[str, any]]:
    """
    Get a list of all agent types in hierarchical order with their info.
    
    Returns:
        List of agent type info dictionaries in hierarchical order
    """
    hierarchy_order = [
        AgentType.VIEWER,
        AgentType.CONTRIBUTOR,
        AgentType.CONTENT_MANAGER,
        AgentType.ADMIN,
    ]
    
    return [
        {
            "type": agent_type.value,
            **get_agent_type_display_info(agent_type)
        }
        for agent_type in hierarchy_order
    ]
