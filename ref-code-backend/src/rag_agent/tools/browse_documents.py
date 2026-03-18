"""
Tool for browsing documents in a RAG corpus via the web interface.
"""

import os
import logging

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

from .utils import check_corpus_exists, get_corpus_resource_name, check_user_corpus_access


def browse_documents(
    corpus_name: str,
    tool_context: ToolContext,
) -> dict:
    """
    Generate a link to browse documents in a specific corpus.
    
    This tool provides a user-friendly interface for viewing all documents in a corpus.
    The user can click on documents to preview them (PDFs) or download them (other formats).

    Args:
        corpus_name (str): The name of the corpus to browse documents from.
        tool_context (ToolContext): The tool context

    Returns:
        dict: A response with a clickable link to the document browser
    """
    # Get agent context for logging
    account_env = os.environ.get("ACCOUNT_ENV", "unknown")
    
    logger.info(f"[{account_env}] Generating document browser link for corpus '{corpus_name}'", 
                extra={"agent": account_env, "corpus": corpus_name, "action": "browse_documents"})
    
    try:
        # Check if the user has access to this corpus
        if not check_user_corpus_access(corpus_name, tool_context):
            logger.warning(
                f"[{account_env}] Corpus access denied for '{corpus_name}'",
                extra={"agent": account_env, "corpus": corpus_name, "action": "browse_documents"}
            )
            return {
                "status": "error",
                "message": f"Access denied: you do not have permission to browse corpus '{corpus_name}'. "
                           f"Your accessible corpora: {tool_context.state.get('accessible_corpus_names', [])}",
                "corpus_name": corpus_name,
            }

        # Check if corpus exists
        if not check_corpus_exists(corpus_name, tool_context):
            return {
                "status": "error",
                "message": f"Corpus '{corpus_name}' does not exist. Please check the corpus name and try again.",
                "corpus_name": corpus_name,
            }

        # Get the frontend URL from environment or use default
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        
        # Generate the document browser URL with corpus pre-selected
        browser_url = f"{frontend_url}/test-documents?corpus={corpus_name}"
        
        logger.info(f"[{account_env}] Generated browser link for corpus '{corpus_name}': {browser_url}", 
                   extra={"agent": account_env, "corpus": corpus_name, "url": browser_url})
        
        return {
            "status": "success",
            "message": f"I've prepared the document browser for you. You can view all documents in the '{corpus_name}' corpus.",
            "corpus_name": corpus_name,
            "browser_url": browser_url,
            "instructions": [
                f"Click the link to open the document browser: {browser_url}",
                "The page will show all documents in the selected corpus",
                "Click on any document name to preview it (PDFs) or download it (other formats)",
                "You can also switch to a different corpus using the dropdown"
            ]
        }

    except Exception as e:
        logger.error(f"[{account_env}] Error generating document browser link for '{corpus_name}': {str(e)}", 
                    extra={"agent": account_env, "corpus": corpus_name, "error": str(e)})
        return {
            "status": "error",
            "message": f"Error generating document browser link: {str(e)}",
            "corpus_name": corpus_name,
        }
