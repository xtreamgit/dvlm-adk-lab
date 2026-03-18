"""
Tool registry for dynamic agent tool loading.
Maps tool names to actual Python tool functions.
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Initialize tool registry
TOOL_REGISTRY: Dict[str, Any] = {}

def register_tools():
    """
    Register all available tools from rag_agent.
    This is called lazily to avoid circular imports.
    """
    global TOOL_REGISTRY
    
    if TOOL_REGISTRY:
        return TOOL_REGISTRY
    
    try:
        from rag_agent.tools.rag_query import rag_query
        from rag_agent.tools.rag_multi_query import rag_multi_query
        from rag_agent.tools.list_corpora import list_corpora
        from rag_agent.tools.create_corpus import create_corpus
        from rag_agent.tools.add_data import add_data
        from rag_agent.tools.get_corpus_info import get_corpus_info
        from rag_agent.tools.delete_corpus import delete_corpus
        from rag_agent.tools.delete_document import delete_document
        from rag_agent.tools.retrieve_document import retrieve_document
        from rag_agent.tools.browse_documents import browse_documents
        from rag_agent.tools.utils import set_current_corpus
        
        TOOL_REGISTRY.update({
            "rag_query": rag_query,
            "rag_multi_query": rag_multi_query,
            "list_corpora": list_corpora,
            "create_corpus": create_corpus,
            "add_data": add_data,
            "get_corpus_info": get_corpus_info,
            "delete_corpus": delete_corpus,
            "delete_document": delete_document,
            "retrieve_document": retrieve_document,
            "browse_documents": browse_documents,
            "set_current_corpus": set_current_corpus,
        })
        
        logger.info(f"Registered {len(TOOL_REGISTRY)} tools in registry")
    except Exception as e:
        logger.error(f"Failed to register tools: {e}")
        raise
    
    return TOOL_REGISTRY

def get_tools_by_names(tool_names: List[str]) -> List[Any]:
    """
    Get tool functions by their names.
    
    Args:
        tool_names: List of tool names from JSON config
        
    Returns:
        List of tool functions
        
    Raises:
        ValueError: If tool name not found in registry
    """
    registry = register_tools()
    
    tools = []
    for tool_name in tool_names:
        if tool_name not in registry:
            available_tools = ", ".join(registry.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found in registry. "
                f"Available tools: {available_tools}"
            )
        tools.append(registry[tool_name])
    
    logger.debug(f"Retrieved {len(tools)} tools: {tool_names}")
    return tools

def get_available_tools() -> List[str]:
    """Get list of all available tool names."""
    registry = register_tools()
    return list(registry.keys())
