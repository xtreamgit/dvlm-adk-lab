"""
Tool for retrieving complete documents from RAG corpora.
Allows agents to help users access full document content.
"""

import os
import logging

from google.adk.tools.tool_context import ToolContext

from .utils import check_corpus_exists, get_corpus_resource_name, get_document_resource_name, check_user_corpus_access

logger = logging.getLogger(__name__)


def retrieve_document(
    corpus_name: str,
    document_name: str,
    tool_context: ToolContext,
) -> dict:
    """
    Retrieve a complete document from a RAG corpus by name.
    
    This tool searches for a document by display name within a specified corpus
    and returns metadata needed for the backend API to generate a signed access URL.
    
    Args:
        corpus_name (str): The name or display name of the corpus containing the document.
        document_name (str): The display name of the document to retrieve.
        tool_context (ToolContext): The tool context for state management.
        
    Returns:
        dict: Document retrieval information with the following structure:
            - status: "success" or "error"
            - message: Human-readable message
            - corpus_name: Name of the corpus
            - document_name: Display name of the document
            - file_id: Vertex AI file ID (if found)
            - source_uri: GCS storage URI (if found)
            - file_type: File extension/type (pdf, txt, docx, etc.)
            
    Example:
        User: "Show me the document about Python hacking in ai-books"
        Agent: retrieve_document(corpus_name="ai-books", document_name="Python Hacking.pdf")
        Returns: {
            "status": "success",
            "message": "Document found. I'll open it for you.",
            "corpus_name": "ai-books",
            "document_name": "Python Hacking.pdf",
            "file_id": "1234567890",
            "source_uri": "gs://dvlm-adk-lab-ai-books/documents/python-hacking.pdf",
            "file_type": "pdf"
        }
    """
    account_env = os.environ.get("ACCOUNT_ENV", "unknown")
    
    logger.info(
        f"[{account_env}] Retrieving document '{document_name}' from corpus '{corpus_name}'",
        extra={"agent": account_env, "corpus": corpus_name, "document": document_name, "action": "retrieve_document"}
    )
    
    try:
        # Step 0: Verify user has access to this corpus
        if not check_user_corpus_access(corpus_name, tool_context):
            logger.warning(
                f"[{account_env}] Corpus access denied for '{corpus_name}'",
                extra={"agent": account_env, "corpus": corpus_name, "action": "retrieve_document"}
            )
            return {
                "status": "error",
                "message": f"Access denied: you do not have permission to access corpus '{corpus_name}'.",
                "corpus_name": corpus_name,
                "document_name": document_name,
                "error_type": "access_denied"
            }

        # Step 1: Verify corpus exists
        if not check_corpus_exists(corpus_name, tool_context):
            logger.warning(
                f"[{account_env}] Corpus '{corpus_name}' not found",
                extra={"agent": account_env, "corpus": corpus_name}
            )
            return {
                "status": "error",
                "message": f"Corpus '{corpus_name}' does not exist. Please verify the corpus name.",
                "corpus_name": corpus_name,
                "document_name": document_name,
                "error_type": "corpus_not_found"
            }
        
        # Step 2: Get corpus resource name
        corpus_resource_name = get_corpus_resource_name(corpus_name)
        
        # Step 3: Search for document by display name
        document_resource_name = get_document_resource_name(corpus_name, document_name)
        
        if not document_resource_name:
            logger.warning(
                f"[{account_env}] Document '{document_name}' not found in corpus '{corpus_name}'",
                extra={"agent": account_env, "corpus": corpus_name, "document": document_name}
            )
            return {
                "status": "error",
                "message": f"Document '{document_name}' not found in corpus '{corpus_name}'. Please check the document name.",
                "corpus_name": corpus_name,
                "document_name": document_name,
                "error_type": "document_not_found",
                "suggestion": "Try using the get_corpus_info tool to list all documents in the corpus."
            }
        
        # Step 4: Extract file ID and metadata
        # Document resource name format: projects/.../locations/.../ragCorpora/.../ragFiles/{file_id}
        file_id = document_resource_name.split('/')[-1]
        
        # Determine file type from document name
        file_type = "unknown"
        if '.' in document_name:
            file_type = document_name.split('.')[-1].lower()
        
        # Step 5: Get source URI (GCS path)
        # This requires calling the RAG API to get file details
        from vertexai import rag
        try:
            files = rag.list_files(corpus_resource_name)
            source_uri = None
            
            for rag_file in files:
                if rag_file.name == document_resource_name:
                    source_uri = rag_file.source_uri if hasattr(rag_file, 'source_uri') else None
                    break
        except Exception as e:
            logger.warning(f"[{account_env}] Could not fetch source URI: {e}")
            source_uri = None
        
        # Get the frontend URL from environment or use default
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        
        # Generate the document viewer URL with corpus and document pre-selected
        from urllib.parse import quote
        viewer_url = f"{frontend_url}/test-documents?corpus={quote(corpus_name)}&document={quote(document_name)}"
        
        logger.info(
            f"[{account_env}] Document found: '{document_name}' (file_id: {file_id})",
            extra={
                "agent": account_env,
                "corpus": corpus_name,
                "document": document_name,
                "file_id": file_id,
                "file_type": file_type
            }
        )
        
        return {
            "status": "success",
            "message": f"I found '{document_name}' in the '{corpus_name}' corpus. Click the link below to open it.",
            "corpus_name": corpus_name,
            "document_name": document_name,
            "file_id": file_id,
            "source_uri": source_uri,
            "file_type": file_type,
            "viewer_url": viewer_url,
            "instructions": [
                f"Click here to open the document: {viewer_url}",
                "The page will automatically load the corpus and highlight the document",
                "Click the document name to preview it (PDFs) or download it (other formats)"
            ]
        }
        
    except Exception as e:
        logger.error(
            f"[{account_env}] Error retrieving document '{document_name}': {str(e)}",
            extra={"agent": account_env, "corpus": corpus_name, "document": document_name, "error": str(e)}
        )
        return {
            "status": "error",
            "message": f"Error retrieving document: {str(e)}",
            "corpus_name": corpus_name,
            "document_name": document_name,
            "error_type": "retrieval_error",
            "error_details": str(e)
        }
