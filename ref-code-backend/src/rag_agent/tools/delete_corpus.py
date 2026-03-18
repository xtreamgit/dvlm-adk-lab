"""
Tool for deleting a Vertex AI RAG corpus when it's no longer needed.
"""

import os
import logging

from google.adk.tools.tool_context import ToolContext
from vertexai import rag

logger = logging.getLogger(__name__)

from .utils import check_corpus_exists, get_corpus_resource_name, check_user_corpus_access


def delete_corpus(
    corpus_name: str,
    confirm: bool,
    tool_context: ToolContext,
) -> dict:
    """
    Delete a Vertex AI RAG corpus when it's no longer needed.
    Requires confirmation to prevent accidental deletion.

    Args:
        corpus_name (str): The full resource name of the corpus to delete.
                           Preferably use the resource_name from list_corpora results.
        confirm (bool): Must be set to True to confirm deletion
        tool_context (ToolContext): The tool context

    Returns:
        dict: Status information about the deletion operation
    """
    # Get agent context for logging
    account_env = os.environ.get("ACCOUNT_ENV", "unknown")
    
    logger.warning(f"[{account_env}] DELETION REQUEST for corpus '{corpus_name}' (confirm={confirm})", 
                   extra={"agent": account_env, "corpus": corpus_name, "action": "delete_corpus", "confirm": confirm})
    
    # Check if the user has access to this corpus
    if not check_user_corpus_access(corpus_name, tool_context):
        logger.warning(
            f"[{account_env}] Corpus access denied for deletion of '{corpus_name}'",
            extra={"agent": account_env, "corpus": corpus_name, "action": "delete_corpus"}
        )
        return {
            "status": "error",
            "message": f"Access denied: you do not have permission to delete corpus '{corpus_name}'.",
            "corpus_name": corpus_name,
        }

    # Check if corpus exists
    if not check_corpus_exists(corpus_name, tool_context):
        return {
            "status": "error",
            "message": f"Corpus '{corpus_name}' does not exist",
            "corpus_name": corpus_name,
        }

    # Check if deletion is confirmed
    if not confirm:
        return {
            "status": "error",
            "message": "Deletion requires explicit confirmation. Set confirm=True to delete this corpus.",
            "corpus_name": corpus_name,
        }

    try:
        # Get the corpus resource name
        corpus_resource_name = get_corpus_resource_name(corpus_name)

        # Delete the corpus
        rag.delete_corpus(corpus_resource_name)

        # Remove from state by setting to False
        state_key = f"corpus_exists_{corpus_name}"
        if state_key in tool_context.state:
            tool_context.state[state_key] = False

        logger.warning(f"[{account_env}] CORPUS DELETED: '{corpus_name}' (resource: {corpus_resource_name})", 
                      extra={"agent": account_env, "corpus": corpus_name, "resource_name": corpus_resource_name})
        return {
            "status": "success",
            "message": f"Successfully deleted corpus '{corpus_name}'",
            "corpus_name": corpus_name,
        }
    except Exception as e:
        logger.error(f"[{account_env}] Error deleting corpus '{corpus_name}': {str(e)}", 
                    extra={"agent": account_env, "corpus": corpus_name, "error": str(e)})
        return {
            "status": "error",
            "message": f"Error deleting corpus: {str(e)}",
            "corpus_name": corpus_name,
        }
