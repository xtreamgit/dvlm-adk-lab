"""
Tool for creating a new Vertex AI RAG corpus.
"""

import os
import logging
import re

from google.adk.tools.tool_context import ToolContext
import vertexai
from vertexai import rag
from ..config import PROJECT_ID, LOCATION

logger = logging.getLogger(__name__)

# Ensure vertexai is initialized for this module
if os.getenv("VALIDATE_CORPORA_WITH_VERTEX", "true").lower() == "true":
    try:
        import google.auth
        credentials, _ = google.auth.default()
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
        print(f"DEBUG: Initialized vertexai in create_corpus with project={PROJECT_ID}, location={LOCATION}")
    except Exception as e:
        print(f"DEBUG: Failed to initialize vertexai in create_corpus: {e}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")

from ..config import (
    DEFAULT_EMBEDDING_MODEL,
)
from .utils import check_corpus_exists


def create_corpus(
    corpus_name: str,
    tool_context: ToolContext,
) -> dict:
    """
    Create a new Vertex AI RAG corpus with the specified name.

    Args:
        corpus_name (str): The name for the new corpus
        tool_context (ToolContext): The tool context for state management

    Returns:
        dict: Status information about the operation
    """
    # Get agent context for logging
    account_env = os.environ.get("ACCOUNT_ENV", "unknown")
    
    user_email = tool_context.state.get("user_email", "unknown")
    logger.info(f"[{account_env}] User '{user_email}' attempting to create corpus '{corpus_name}'", 
                extra={"agent": account_env, "corpus": corpus_name, "action": "create_corpus", "user_email": user_email})
    
    # Check if corpus already exists
    if check_corpus_exists(corpus_name, tool_context):
        logger.info(f"[{account_env}] Corpus '{corpus_name}' already exists", 
                   extra={"agent": account_env, "corpus": corpus_name})
        return {
            "status": "info",
            "message": f"Corpus '{corpus_name}' already exists",
            "corpus_name": corpus_name,
            "corpus_created": False,
        }

    try:
        # Clean corpus name for use as display name
        display_name = re.sub(r"[^a-zA-Z0-9_-]", "_", corpus_name)

        # Configure embedding model
        embedding_model_config = rag.RagEmbeddingModelConfig(
            vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                publisher_model=DEFAULT_EMBEDDING_MODEL
            )
        )

        # Create the corpus
        rag_corpus = rag.create_corpus(
            display_name=display_name,
            backend_config=rag.RagVectorDbConfig(
                rag_embedding_model_config=embedding_model_config
            ),
        )

        # Update state to track corpus existence
        tool_context.state[f"corpus_exists_{corpus_name}"] = True

        # Set this as the current corpus
        tool_context.state["current_corpus"] = corpus_name

        logger.info(f"[{account_env}] Successfully created corpus '{corpus_name}' with resource name: {rag_corpus.name}", 
                   extra={"agent": account_env, "corpus": corpus_name, "resource_name": rag_corpus.name})
        return {
            "status": "success",
            "message": f"Successfully created corpus '{corpus_name}'",
            "corpus_name": rag_corpus.name,
            "display_name": rag_corpus.display_name,
            "corpus_created": True,
        }

    except Exception as e:
        logger.error(f"[{account_env}] Error creating corpus '{corpus_name}': {str(e)}", 
                    extra={"agent": account_env, "corpus": corpus_name, "error": str(e)})
        return {
            "status": "error",
            "message": f"Error creating corpus: {str(e)}",
            "corpus_name": corpus_name,
            "corpus_created": False,
        }
