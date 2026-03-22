"""
Tool for querying Vertex AI RAG corpora and retrieving relevant information.
"""

import logging

from google.adk.tools.tool_context import ToolContext
import vertexai
from vertexai import rag
from ..config import PROJECT_ID, LOCATION

# Ensure vertexai is initialized for this module
import os
if os.getenv("VALIDATE_CORPORA_WITH_VERTEX", "true").lower() == "true":
    try:
        import google.auth
        credentials, _ = google.auth.default()
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
        print(f"DEBUG: Initialized vertexai in rag_query with project={PROJECT_ID}, location={LOCATION}")
    except Exception as e:
        print(f"DEBUG: Failed to initialize vertexai in rag_query: {e}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")

from ..config import (
    DEFAULT_DISTANCE_THRESHOLD,
    DEFAULT_TOP_K,
)
from .utils import check_corpus_exists, get_corpus_resource_name, check_user_corpus_access


def rag_query(
    corpus_name: str,
    query: str,
    tool_context: ToolContext,
) -> dict:
    """
    Query a Vertex AI RAG corpus with a user question and return relevant information.

    Args:
        corpus_name (str): The name of the corpus to query. If empty, the current corpus will be used.
                          Preferably use the resource_name from list_corpora results.
        query (str): The text query to search for in the corpus
        tool_context (ToolContext): The tool context

    Returns:
        dict: The query results and status
    """
    # Get agent context for logging
    import os
    account_env = os.environ.get("ACCOUNT_ENV", "unknown")
    
    try:
        logging.info(f"[{account_env}] Querying corpus '{corpus_name}' with query: {query[:50]}...", 
                    extra={"agent": account_env, "corpus": corpus_name, "action": "rag_query"})

        # Check if the user has access to this corpus
        if not check_user_corpus_access(corpus_name, tool_context):
            logging.warning(
                f"[{account_env}] Corpus access denied for '{corpus_name}'",
                extra={"agent": account_env, "corpus": corpus_name, "action": "rag_query"}
            )
            return {
                "status": "error",
                "message": f"Access denied: you do not have permission to query corpus '{corpus_name}'. "
                           f"Your accessible corpora: {tool_context.state.get('accessible_corpus_names', [])}",
                "query": query,
                "corpus_name": corpus_name,
            }

        # Check if the corpus exists
        if not check_corpus_exists(corpus_name, tool_context):
            return {
                "status": "error",
                "message": f"Corpus '{corpus_name}' does not exist. Please create it first using the create_corpus tool.",
                "query": query,
                "corpus_name": corpus_name,
            }

        # Get the corpus resource name
        corpus_resource_name = get_corpus_resource_name(corpus_name)

        # Configure retrieval parameters
        rag_retrieval_config = rag.RagRetrievalConfig(
            top_k=DEFAULT_TOP_K,
            filter=rag.Filter(vector_distance_threshold=DEFAULT_DISTANCE_THRESHOLD),
        )

        # Perform the query
        print("Performing retrieval query...")
        response = rag.retrieval_query(
            rag_resources=[
                rag.RagResource(
                    rag_corpus=corpus_resource_name,
                )
            ],
            text=query,
            rag_retrieval_config=rag_retrieval_config,
        )

        # Process the response into a more usable format
        results = []
        if hasattr(response, "contexts") and response.contexts:
            for ctx_group in response.contexts.contexts:
                result = {
                    "source_uri": (
                        ctx_group.source_uri if hasattr(ctx_group, "source_uri") else ""
                    ),
                    "source_name": (
                        ctx_group.source_display_name
                        if hasattr(ctx_group, "source_display_name")
                        else ""
                    ),
                    "text": ctx_group.text if hasattr(ctx_group, "text") else "",
                    "score": ctx_group.score if hasattr(ctx_group, "score") else 0.0,
                }
                results.append(result)

        # If we didn't find any results
        if not results:
            logging.warning(f"[{account_env}] No results found in corpus '{corpus_name}'", 
                          extra={"agent": account_env, "corpus": corpus_name, "results_count": 0})
            return {
                "status": "warning",
                "message": f"No results found in corpus '{corpus_name}' for query: '{query}'",
                "query": query,
                "corpus_name": corpus_name,
                "results": [],
                "results_count": 0,
            }

        logging.info(f"[{account_env}] Query successful - found {len(results)} results", 
                    extra={"agent": account_env, "corpus": corpus_name, "results_count": len(results)})
        return {
            "status": "success",
            "message": f"Successfully queried corpus '{corpus_name}'",
            "query": query,
            "corpus_name": corpus_name,
            "results": results,
            "results_count": len(results),
        }

    except Exception as e:
        error_msg = f"Error querying corpus: {str(e)}"
        logging.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "query": query,
            "corpus_name": corpus_name,
        }
