"""
Document retrieval API routes.
Handles document search, signed URL generation, and access control.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.corpus_service import CorpusService
from services.document_service import DocumentService
from models.user import User
from middleware.iap_auth_middleware import get_current_user_iap as get_current_user_hybrid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


class DocumentRetrievalResponse(BaseModel):
    """Response model for document retrieval."""
    status: str
    document: dict
    access: Optional[dict] = None


@router.get("/retrieve", response_model=DocumentRetrievalResponse)
async def retrieve_document(
    corpus_id: int,
    document_name: str,
    generate_url: bool = True,
    request: Request = None,
    current_user: User = Depends(get_current_user_hybrid)
):
    """
    Retrieve a document from a corpus and generate signed access URL.
    
    **Security**: User must have 'read' access to the corpus.
    
    **Parameters**:
    - **corpus_id**: ID of the corpus containing the document
    - **document_name**: Display name of the document to retrieve
    - **generate_url**: Whether to generate a signed URL (default: true)
    
    **Returns**:
    - Document metadata
    - Signed GCS URL (if generate_url=true)
    - URL expiration time
    
    **Access Control**:
    1. Validates user has access to corpus
    2. Searches for document in Vertex AI RAG
    3. Generates time-limited signed URL (30 minutes)
    4. Logs access attempt to audit trail
    """
    
    # Step 1: Validate corpus access
    if not CorpusService.validate_corpus_access(current_user.id, corpus_id):
        logger.warning(
            f"User {current_user.email} (ID: {current_user.id}) "
            f"denied access to corpus {corpus_id}"
        )
        
        # Log failed access attempt
        DocumentService.log_access(
            user_id=current_user.id,
            corpus_id=corpus_id,
            document_name=document_name,
            success=False,
            error_message="User does not have access to corpus",
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get('user-agent') if request else None
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this corpus"
        )
    
    # Step 2: Get corpus details
    corpus = CorpusService.get_corpus_by_id(corpus_id)
    if not corpus:
        logger.error(f"Corpus {corpus_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found"
        )
    
    if not corpus.vertex_corpus_id:
        logger.error(f"Corpus {corpus_id} has no vertex_corpus_id")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Corpus is not properly configured"
        )
    
    # Step 3: Search for document in Vertex AI RAG
    document = DocumentService.find_document(corpus.vertex_corpus_id, document_name)
    
    if not document:
        logger.warning(
            f"Document '{document_name}' not found in corpus '{corpus.name}' "
            f"(ID: {corpus_id})"
        )
        
        # Log failed access attempt
        DocumentService.log_access(
            user_id=current_user.id,
            corpus_id=corpus_id,
            document_name=document_name,
            success=False,
            error_message="Document not found in corpus",
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get('user-agent') if request else None
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_name}' not found in corpus '{corpus.name}'"
        )
    
    # Step 4: Get additional metadata from GCS
    metadata = {}
    if document.get('source_uri'):
        metadata = DocumentService.get_document_metadata(document['source_uri'])
    
    # Step 5: Generate signed URL if requested
    signed_url = None
    expires_at = None
    valid_for_seconds = None
    
    logger.info(f"[DEBUG] generate_url={generate_url}, document.source_uri={document.get('source_uri')}")
    
    if generate_url and document.get('source_uri'):
        logger.info(f"[DEBUG] Generating signed URL for: {document['source_uri']}")
        signed_url, expires_at = DocumentService.generate_signed_url(
            document['source_uri'],
            expiration_minutes=30
        )
        logger.info(f"[DEBUG] Generated signed_url={'<url>' if signed_url else 'None'}, expires_at={expires_at}")
        
        if not signed_url:
            logger.warning(
                f"Could not generate signed URL for {document['source_uri']}. "
                f"Document metadata will be returned without a direct URL; "
                f"the frontend proxy endpoint can still stream the file."
            )
        
        valid_for_seconds = 1800  # 30 minutes
    
    # Step 6: Log successful access
    DocumentService.log_access(
        user_id=current_user.id,
        corpus_id=corpus_id,
        document_name=document_name,
        document_file_id=document.get('file_id'),
        source_uri=document.get('source_uri'),
        success=True,
        access_type='view',
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get('user-agent') if request else None
    )
    
    logger.info(
        f"Document retrieval successful: user={current_user.email}, "
        f"corpus={corpus.name}, document={document_name}"
    )
    
    # Step 7: Build response
    response_document = {
        'id': document.get('file_id'),
        'name': document.get('display_name'),
        'corpus_id': corpus_id,
        'corpus_name': corpus.name,
        'file_type': document.get('file_type', 'unknown'),
        'size_bytes': metadata.get('size_bytes'),
        'created_at': document.get('created_at'),
        'updated_at': document.get('updated_at'),
        'source_uri': document.get('source_uri'),  # Include source_uri to avoid duplicate lookups
    }
    
    response_access = None
    if signed_url:
        response_access = {
            'url': signed_url,
            'expires_at': expires_at.isoformat() if expires_at else None,
            'valid_for_seconds': valid_for_seconds
        }
    
    return DocumentRetrievalResponse(
        status="success",
        document=response_document,
        access=response_access
    )


@router.get("/corpus/{corpus_id}/list")
async def list_corpus_documents(
    corpus_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_user_hybrid)
):
    """
    List all documents in a corpus.
    
    **Security**: User must have access to the corpus.
    
    **Parameters**:
    - **corpus_id**: ID of the corpus
    
    **Returns**: List of documents with metadata
    """
    # Validate corpus access
    if not CorpusService.validate_corpus_access(current_user.id, corpus_id):
        logger.warning(
            f"User {current_user.email} (ID: {current_user.id}) "
            f"denied access to list documents in corpus {corpus_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this corpus"
        )
    
    # Get corpus details
    corpus = CorpusService.get_corpus_by_id(corpus_id)
    if not corpus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found"
        )
    
    if not corpus.vertex_corpus_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Corpus is not properly configured"
        )
    
    # Get documents from Vertex AI
    try:
        documents = DocumentService.list_documents(corpus.vertex_corpus_id)
        logger.info(
            f"Listed {len(documents)} documents from corpus '{corpus.name}' "
            f"for user {current_user.email}"
        )
        return {
            "status": "success",
            "corpus_id": corpus_id,
            "corpus_name": corpus.name,
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        logger.error(f"Error listing documents in corpus {corpus_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/proxy/{corpus_id}/{document_name}")
async def proxy_document(
    corpus_id: int,
    document_name: str,
    source_uri: Optional[str] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user_hybrid)
):
    """
    Proxy endpoint to stream PDF documents from GCS with proper CORS headers.
    
    This solves the CORS issue where PDF.js cannot load PDFs directly from
    GCS signed URLs because they don't include access-control headers.
    
    **Security**: User must have 'read' access to the corpus.
    
    **Parameters**:
    - **corpus_id**: ID of the corpus containing the document
    - **document_name**: Display name of the document to retrieve
    - **source_uri**: Optional GCS URI to skip document lookup (performance optimization)
    
    **Returns**: Streamed PDF content with proper CORS headers
    """
    # Validate corpus access
    if not CorpusService.validate_corpus_access(current_user.id, corpus_id):
        logger.warning(
            f"User {current_user.email} (ID: {current_user.id}) "
            f"denied access to proxy document in corpus {corpus_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this corpus"
        )
    
    # Get corpus details (needed for logging)
    corpus = CorpusService.get_corpus_by_id(corpus_id)
    if not corpus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found"
        )
    
    # If source_uri provided, use it directly (skip document lookup)
    if source_uri:
        logger.info(
            f"Using provided source_uri for document '{document_name}' "
            f"in corpus {corpus_id} (skipping Vertex AI lookup)"
        )
        document_source_uri = source_uri
        file_id = None
    else:
        # Fall back to name-based lookup
        if not corpus.vertex_corpus_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Corpus not properly configured"
            )
        
        # Find document and get source_uri
        document = DocumentService.find_document(corpus.vertex_corpus_id, document_name)
        if not document or not document.get('source_uri'):
            logger.error(
                f"Document '{document_name}' not found in corpus {corpus_id}. "
                f"This may be due to name mismatch. Consider passing source_uri parameter."
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        document_source_uri = document['source_uri']
        file_id = document.get('file_id')
    
    # Stream directly from GCS using the default SA credentials (no signing needed)
    try:
        reader, content_type, size = DocumentService.stream_from_gcs(document_source_uri)

        def _iter_reader():
            try:
                while True:
                    chunk = reader.read(8192)
                    if not chunk:
                        break
                    yield chunk
            finally:
                reader.close()

        # Log successful access
        DocumentService.log_access(
            user_id=current_user.id,
            corpus_id=corpus_id,
            document_name=document_name,
            document_file_id=file_id,
            source_uri=document_source_uri,
            success=True,
            access_type='view',
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get('user-agent') if request else None
        )

        logger.info(
            f"Proxying document: user={current_user.email}, "
            f"corpus={corpus.name}, document={document_name}"
        )

        headers = {
            "Content-Disposition": f'inline; filename="{document_name}"',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
        if size:
            headers["Content-Length"] = str(size)

        return StreamingResponse(
            _iter_reader(),
            media_type=content_type,
            headers=headers,
        )
    except Exception as e:
        logger.error(f"Error streaming document from GCS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document from storage"
        )


@router.get("/access-logs")
async def get_document_access_logs(
    limit: int = 100,
    request: Request = None,
    current_user: User = Depends(get_current_user_hybrid)
):
    """
    Get document access logs for current user.
    
    **Parameters**:
    - **limit**: Maximum number of records to return (default: 100, max: 500)
    
    **Returns**: List of access log entries
    """
    # Limit the maximum to prevent abuse
    limit = min(limit, 500)
    
    logs = DocumentService.get_access_logs(
        user_id=current_user.id,
        limit=limit
    )
    
    return {
        "logs": logs,
        "count": len(logs),
        "user": current_user.email
    }


@router.get("/corpus/{corpus_id}/access-logs")
async def get_corpus_access_logs(
    corpus_id: int,
    limit: int = 100,
    request: Request = None,
    current_user: User = Depends(get_current_user_hybrid)
):
    """
    Get document access logs for a specific corpus.
    
    **Security**: User must have access to the corpus.
    
    **Parameters**:
    - **corpus_id**: Corpus ID
    - **limit**: Maximum number of records to return
    
    **Returns**: List of access log entries for the corpus
    """
    # Validate corpus access
    if not CorpusService.validate_corpus_access(current_user.id, corpus_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this corpus"
        )
    
    # Limit the maximum
    limit = min(limit, 500)
    
    logs = DocumentService.get_access_logs(
        user_id=current_user.id,
        corpus_id=corpus_id,
        limit=limit
    )
    
    return {
        "logs": logs,
        "count": len(logs),
        "corpus_id": corpus_id,
        "user": current_user.email
    }
