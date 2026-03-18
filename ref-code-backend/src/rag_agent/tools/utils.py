"""
Utility functions for the RAG tools.
"""

import os
import logging
import re

from google.adk.tools.tool_context import ToolContext
from vertexai import rag

from ..config import (
    LOCATION,
    PROJECT_ID,
)

logger = logging.getLogger(__name__)


def get_accessible_corpus_names(tool_context: ToolContext) -> list:
    """
    Get the list of corpus names the current user is authorized to access.
    
    Returns the list from session state, or an empty list if not set.
    An empty list means no corpus access restrictions are enforced
    (e.g., admin users or when the bridge is not configured).
    """
    return tool_context.state.get("accessible_corpus_names", [])


def check_user_corpus_access(corpus_name: str, tool_context: ToolContext) -> bool:
    """
    Check if the current user has access to a specific corpus.
    
    Reads the user's accessible corpus list from the ADK session state
    (injected by server.py from the chatbot_corpus_access table).
    
    Args:
        corpus_name: The display name of the corpus to check access for.
        tool_context: The ADK tool context containing session state.
        
    Returns:
        True if the user has access, False otherwise.
        If no access list is set in state, returns True (permissive fallback).
    """
    accessible = tool_context.state.get("accessible_corpus_names")
    
    # If no access list is set, allow access (backward compatibility / admin fallback)
    if accessible is None:
        return True
    
    # Empty list means the user has no corpus access at all
    if not accessible:
        return False
    
    # Check if the corpus name matches any accessible corpus
    # Handle both display names and resource names
    for allowed_name in accessible:
        if corpus_name == allowed_name:
            return True
        # Also match if the corpus_name is a resource name ending with the allowed name
        if corpus_name.endswith(f"/{allowed_name}"):
            return True
        # Also match if the allowed_name appears as the display name in a resource path
        if allowed_name.endswith(f"/{corpus_name}"):
            return True
    
    return False


def get_document_resource_name(corpus_name: str, document_name: str) -> str | None:
    """
    Finds the full resource name for a document within a corpus by its display name.

    Args:
        corpus_name (str): The name of the corpus.
        document_name (str): The display name of the document.

    Returns:
        str | None: The full resource name of the document, or None if not found.
    """
    try:
        corpus_resource_name = get_corpus_resource_name(corpus_name)
        if not corpus_resource_name:
            return None

        # List files in the corpus to find the matching document
        response = rag.list_files(corpus_resource_name)

        for file in response:
            if file.display_name.strip().lower() == document_name.strip().lower():
                logger.info(f"Found document '{document_name}' with resource name: {file.name}")
                return file.name

        logger.warning(f"Document '{document_name}' not found in corpus '{corpus_name}'.")
        return None
    except Exception as e:
        logger.error(f"Error retrieving document '{document_name}': {e}")
        return None



def get_corpus_resource_name(corpus_name: str) -> str:
    """
    Convert a corpus name to its full resource name if needed.
    Handles various input formats and ensures the returned name follows Vertex AI's requirements.

    Args:
        corpus_name (str): The corpus name or display name

    Returns:
        str: The full resource name of the corpus
    """
    logger.info(f"Getting resource name for corpus: {corpus_name}")

    # If it's already a full resource name with the projects/locations/ragCorpora format
    if re.match(r"^projects/[^/]+/locations/[^/]+/ragCorpora/[^/]+$", corpus_name):
        return corpus_name

    # Check if this is a display name of an existing corpus
    try:
        # List all corpora and check if there's a match with the display name
        corpora = rag.list_corpora()
        for corpus in corpora:
            if hasattr(corpus, "display_name") and corpus.display_name == corpus_name:
                logger.info(
                    f"Found corpus with display name '{corpus_name}'. Resource name: {corpus.name}"
                )
                return corpus.name
    except Exception as e:
        logger.warning(f"Error when checking for corpus display name: {str(e)}")
        # If we can't check, continue with the default behavior
        pass

    # If it contains partial path elements, extract just the corpus ID
    if "/" in corpus_name:
        # Extract the last part of the path as the corpus ID
        corpus_id = corpus_name.split("/")[-1]
    else:
        corpus_id = corpus_name

    # Remove any special characters that might cause issues
    corpus_id = re.sub(r"[^a-zA-Z0-9_-]", "_", corpus_id)

    # Construct the standardized resource name
    return f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{corpus_id}"


def check_corpus_exists(corpus_name: str, tool_context: ToolContext) -> bool:
    """
    Check if a corpus with the given name exists.

    Args:
        corpus_name (str): The name of the corpus to check
        tool_context (ToolContext): The tool context for state management

    Returns:
        bool: True if the corpus exists, False otherwise
    """
    account_env = os.environ.get("ACCOUNT_ENV", "unknown")
    
    # Check state first if tool_context is provided
    if tool_context.state.get(f"corpus_exists_{corpus_name}"):
        return True

    try:
        # Get full resource name
        corpus_resource_name = get_corpus_resource_name(corpus_name)

        # List all corpora and check if this one exists
        corpora = rag.list_corpora()
        for corpus in corpora:
            if (
                corpus.name == corpus_resource_name
                or corpus.display_name == corpus_name
            ):
                # Update state
                tool_context.state[f"corpus_exists_{corpus_name}"] = True
                # Also set this as the current corpus if no current corpus is set
                if not tool_context.state.get("current_corpus"):
                    tool_context.state["current_corpus"] = corpus_name
                logger.debug(f"[{account_env}] Corpus '{corpus_name}' exists", 
                           extra={"agent": account_env, "corpus": corpus_name})
                return True

        logger.debug(f"[{account_env}] Corpus '{corpus_name}' not found", 
                    extra={"agent": account_env, "corpus": corpus_name})
        return False
    except Exception as e:
        logger.error(f"[{account_env}] Error checking if corpus exists: {str(e)}", 
                    extra={"agent": account_env, "corpus": corpus_name, "error": str(e)})
        # If we can't check, assume it doesn't exist
        return False


def set_current_corpus(corpus_name: str, tool_context: ToolContext) -> bool:
    """
    Set the current corpus in the tool context state.

    Args:
        corpus_name (str): The name of the corpus to set as current
        tool_context (ToolContext): The tool context for state management

    Returns:
        bool: True if the corpus exists and was set as current, False otherwise
    """
    # Check if the user has access to this corpus
    if not check_user_corpus_access(corpus_name, tool_context):
        logger.warning(
            f"Corpus access denied for set_current_corpus: '{corpus_name}'",
        )
        return False

    # Check if corpus exists first
    if check_corpus_exists(corpus_name, tool_context):
        tool_context.state["current_corpus"] = corpus_name
        return True
    return False
