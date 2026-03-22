"""
Tool for listing all available Vertex AI RAG corpora.
"""

import os
import logging
from typing import Dict, List, Union

from google.adk.tools.tool_context import ToolContext
import vertexai
from vertexai import rag
from ..config import PROJECT_ID, LOCATION
from .utils import check_user_corpus_access

logger = logging.getLogger(__name__)

# Ensure vertexai is initialized for this module
if os.getenv("VALIDATE_CORPORA_WITH_VERTEX", "true").lower() == "true":
    try:
        import google.auth
        credentials, _ = google.auth.default()
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
        print(f"DEBUG: Initialized vertexai in list_corpora with project={PROJECT_ID}, location={LOCATION}")
    except Exception as e:
        print(f"DEBUG: Failed to initialize vertexai in list_corpora: {e}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")


def list_corpora(tool_context: ToolContext) -> dict:
    """
    List all available Vertex AI RAG corpora.

    Returns:
        dict: A list of available corpora and status, with each corpus containing:
            - resource_name: The full resource name to use with other tools
            - display_name: The human-readable name of the corpus
            - create_time: When the corpus was created
            - update_time: When the corpus was last updated
    """
    # Get agent context for logging
    account_env = os.environ.get("ACCOUNT_ENV", "unknown")
    
    try:
        logger.info(f"[{account_env}] Listing all corpora", extra={"agent": account_env, "action": "list_corpora"})

        if os.getenv("VALIDATE_CORPORA_WITH_VERTEX", "true").lower() != "true":
            logger.debug(
                f"[{account_env}] list_corpora state debug: keys={list(tool_context.state.keys())}, "
                f"user_id={tool_context.state.get('user_id')}, "
                f"accessible_corpus_names={tool_context.state.get('accessible_corpus_names')}",
                extra={"agent": account_env},
            )
            user_id = tool_context.state.get("user_id")
            accessible = None
            if user_id is not None:
                try:
                    from database.repositories.corpus_repository import CorpusRepository

                    accessible_rows = CorpusRepository.get_user_corpora(int(user_id), active_only=True)
                    accessible = [row["name"] for row in accessible_rows]
                except Exception as e:
                    logger.warning(
                        f"[{account_env}] Failed to fetch accessible corpora from DB in list_corpora: {e}",
                        extra={"agent": account_env},
                    )

            if accessible is None:
                accessible = tool_context.state.get("accessible_corpus_names")

            if accessible is None:
                accessible = []
            corpus_info = [
                {
                    "resource_name": name,
                    "display_name": name,
                    "create_time": "",
                    "update_time": "",
                }
                for name in accessible
            ]
            logger.info(
                f"[{account_env}] Found {len(corpus_info)} accessible corpora (db-backed)",
                extra={"agent": account_env, "count": len(corpus_info)},
            )
            return {
                "status": "success",
                "message": f"Found {len(corpus_info)} available corpora",
                "corpora": corpus_info,
            }

        # Get the list of corpora
        corpora = rag.list_corpora()

        # Process corpus information into a more usable format
        corpus_info: List[Dict[str, Union[str, int]]] = []
        for corpus in corpora:
            corpus_data: Dict[str, Union[str, int]] = {
                "resource_name": corpus.name,  # Full resource name for use with other tools
                "display_name": corpus.display_name,
                "create_time": (
                    str(corpus.create_time) if hasattr(corpus, "create_time") else ""
                ),
                "update_time": (
                    str(corpus.update_time) if hasattr(corpus, "update_time") else ""
                ),
            }

            corpus_info.append(corpus_data)

        # Filter corpora by user access
        accessible = tool_context.state.get("accessible_corpus_names")
        if accessible is not None:
            filtered_info = [
                c for c in corpus_info
                if c["display_name"] in accessible
            ]
            filtered_count = len(corpus_info) - len(filtered_info)
            if filtered_count > 0:
                logger.info(
                    f"[{account_env}] Filtered {filtered_count} corpora the user cannot access",
                    extra={"agent": account_env, "filtered": filtered_count}
                )
            corpus_info = filtered_info

        logger.info(f"[{account_env}] Found {len(corpus_info)} accessible corpora", extra={"agent": account_env, "count": len(corpus_info)})
        return {
            "status": "success",
            "message": f"Found {len(corpus_info)} available corpora",
            "corpora": corpus_info,
        }
    except Exception as e:
        logger.error(f"[{account_env}] Error listing corpora: {str(e)}", extra={"agent": account_env, "error": str(e)})
        return {
            "status": "error",
            "message": f"Error listing corpora: {str(e)}",
            "corpora": [],
        }
