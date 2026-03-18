"""
Document retrieval and management service.
Handles document search, GCS signed URL generation, and access logging.
"""

import logging
import re
import time
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta, timezone

from google.cloud import storage
from vertexai import rag
from google.api_core import exceptions as google_exceptions

from database.connection import get_db_connection

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document operations including retrieval and access control."""
    
    @staticmethod
    def find_document(corpus_resource_name: str, document_name: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Search for document in corpus by display name with retry logic.
        
        Args:
            corpus_resource_name: Full Vertex AI corpus resource name
            document_name: Display name of the document
            max_retries: Maximum retry attempts for rate limit errors (default: 3)
            
        Returns:
            Dictionary with document metadata or None if not found
        """
        for attempt in range(max_retries + 1):
            try:
                files = rag.list_files(corpus_resource_name)
                
                for rag_file in files:
                    # Case-insensitive match on display name
                    if rag_file.display_name.strip().lower() == document_name.strip().lower():
                        # Extract file ID from resource name
                        # Format: projects/.../locations/.../ragCorpora/.../ragFiles/{file_id}
                        file_id = rag_file.name.split('/')[-1]
                        
                        # Determine file type from display name
                        file_extension = document_name.split('.')[-1].lower() if '.' in document_name else 'unknown'
                        
                        # DEBUG: Log all attributes of rag_file object
                        logger.info(f"[DEBUG] RAG file object type: {type(rag_file)}")
                        logger.info(f"[DEBUG] RAG file attributes: {dir(rag_file)}")
                        logger.info(f"[DEBUG] RAG file dict representation: {rag_file.__dict__ if hasattr(rag_file, '__dict__') else 'no __dict__'}")
                        
                        # Extract source_uri - try different attribute access methods
                        source_uri = None
                        if hasattr(rag_file, 'rag_file_source'):
                            logger.info(f"[DEBUG] Has rag_file_source: {rag_file.rag_file_source}")
                            if hasattr(rag_file.rag_file_source, 'gcs_source'):
                                logger.info(f"[DEBUG] Has gcs_source: {rag_file.rag_file_source.gcs_source}")
                                source_uri = rag_file.rag_file_source.gcs_source.uris[0] if rag_file.rag_file_source.gcs_source.uris else None
                        elif hasattr(rag_file, 'source_uri'):
                            logger.info(f"[DEBUG] Has source_uri attribute")
                            source_uri = rag_file.source_uri
                        elif hasattr(rag_file, 'gcs_source'):
                            logger.info(f"[DEBUG] Has gcs_source attribute")
                            source_uri = rag_file.gcs_source.uris[0] if rag_file.gcs_source.uris else None
                        
                        logger.info(f"[DEBUG] Found document '{document_name}': source_uri={source_uri}")
                        
                        return {
                            'file_id': file_id,
                            'display_name': rag_file.display_name,
                            'source_uri': source_uri,
                            'resource_name': rag_file.name,
                            'file_type': file_extension,
                            'created_at': str(rag_file.create_time) if hasattr(rag_file, 'create_time') else None,
                            'updated_at': str(rag_file.update_time) if hasattr(rag_file, 'update_time') else None,
                        }
                
                logger.info(f"Document '{document_name}' not found in corpus {corpus_resource_name}")
                return None
                
            except google_exceptions.ResourceExhausted as e:
                # 429 RESOURCE_EXHAUSTED - retry with exponential backoff
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + (0.1 * attempt)  # 1s, 2.1s, 4.2s
                    logger.warning(
                        f"Rate limit hit while searching for '{document_name}' "
                        f"(attempt {attempt + 1}/{max_retries + 1}). Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limit exceeded after {max_retries + 1} attempts: {e}")
                    raise
                    
            except Exception as e:
                logger.error(f"Error searching for document '{document_name}': {e}")
                return None
    
    @staticmethod
    def list_documents(corpus_resource_name: str, max_retries: int = 3) -> list:
        """
        List all documents in a corpus with retry logic.
        
        Args:
            corpus_resource_name: Full Vertex AI corpus resource name
            max_retries: Maximum retry attempts for rate limit errors (default: 3)
            
        Returns:
            List of dictionaries with document metadata
        """
        for attempt in range(max_retries + 1):
            try:
                files = rag.list_files(corpus_resource_name)
                documents = []
                
                for rag_file in files:
                    # Extract file ID
                    file_id = rag_file.name.split('/')[-1]
                    
                    # Determine file type
                    display_name = rag_file.display_name
                    file_extension = display_name.split('.')[-1].lower() if '.' in display_name else 'unknown'
                    
                    # Extract source URI
                    source_uri = None
                    if hasattr(rag_file, 'rag_file_source'):
                        if hasattr(rag_file.rag_file_source, 'gcs_source'):
                            source_uri = rag_file.rag_file_source.gcs_source.uris[0] if rag_file.rag_file_source.gcs_source.uris else None
                    elif hasattr(rag_file, 'source_uri'):
                        source_uri = rag_file.source_uri
                    elif hasattr(rag_file, 'gcs_source'):
                        source_uri = rag_file.gcs_source.uris[0] if rag_file.gcs_source.uris else None
                    
                    documents.append({
                        'file_id': file_id,
                        'display_name': display_name,
                        'source_uri': source_uri,
                        'resource_name': rag_file.name,
                        'file_type': file_extension,
                        'created_at': str(rag_file.create_time) if hasattr(rag_file, 'create_time') else None,
                        'updated_at': str(rag_file.update_time) if hasattr(rag_file, 'update_time') else None,
                    })
                
                # Sort alphabetically by display name
                documents.sort(key=lambda x: x['display_name'].lower())
                
                logger.info(f"Listed {len(documents)} documents from corpus {corpus_resource_name}")
                return documents
                
            except google_exceptions.ResourceExhausted as e:
                # 429 RESOURCE_EXHAUSTED - retry with exponential backoff
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + (0.1 * attempt)  # 1s, 2.1s, 4.2s
                    logger.warning(
                        f"Rate limit hit while listing documents from corpus "
                        f"(attempt {attempt + 1}/{max_retries + 1}). Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limit exceeded after {max_retries + 1} attempts: {e}")
                    raise
                    
            except Exception as e:
                logger.error(f"Error listing documents from corpus {corpus_resource_name}: {e}")
                raise
    
    @staticmethod
    def generate_signed_url(
        source_uri: str, 
        expiration_minutes: int = 30
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """
        Generate time-limited signed URL for GCS object.
        
        Args:
            source_uri: GCS URI (gs://bucket/path/to/file)
            expiration_minutes: URL expiration time in minutes (default: 30)
            
        Returns:
            Tuple of (signed_url, expiration_datetime)
        """
        if not source_uri or not source_uri.startswith('gs://'):
            logger.warning(f"Invalid source URI for signed URL generation: {source_uri}")
            return None, None
        
        try:
            # Parse GCS URI
            match = re.match(r'gs://([^/]+)/(.+)', source_uri)
            if not match:
                return None, None
            
            bucket_name = match.group(1)
            object_path = match.group(2)
            
            # Initialize GCS client
            from google.auth import default
            from google.auth import compute_engine
            from google.auth import impersonated_credentials
            
            credentials, project = default()
            
            # Check if credentials support signing directly
            if hasattr(credentials, 'sign_bytes'):
                # Direct signing supported (service account key)
                storage_client = storage.Client(credentials=credentials, project=project)
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(object_path)
                
                expiration = timedelta(minutes=expiration_minutes)
                expires_at = datetime.now(timezone.utc) + expiration
                
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=expiration,
                    method="GET"
                )
                
                logger.info(f"Generated signed URL (direct) for {source_uri}")
                return signed_url, expires_at
            else:
                # Use IAM signBlob for Cloud Run / Compute Engine credentials
                logger.info(f"Using IAM signBlob for {source_uri}")
                
                # Get service account email from credentials or metadata server
                service_account_email = None
                
                # Try to get from credentials object
                if hasattr(credentials, 'service_account_email'):
                    service_account_email = credentials.service_account_email
                    logger.info(f"Got SA email from credentials: {service_account_email}")
                
                # If not available, query metadata server (Cloud Run / GCE)
                if not service_account_email or service_account_email == 'default':
                    try:
                        import requests as req
                        metadata_url = 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email'
                        headers = {'Metadata-Flavor': 'Google'}
                        response = req.get(metadata_url, headers=headers, timeout=2)
                        if response.status_code == 200:
                            service_account_email = response.text.strip()
                            logger.info(f"Got SA email from metadata: {service_account_email}")
                    except Exception as e:
                        logger.error(f"Failed to get SA email from metadata: {e}")
                
                if not service_account_email or service_account_email == 'default':
                    logger.error("Could not determine service account email")
                    return None, None
                
                logger.info(f"Using service account: {service_account_email}")
                
                # Use impersonated credentials for signing
                target_scopes = ['https://www.googleapis.com/auth/devstorage.read_only']
                signing_credentials = impersonated_credentials.Credentials(
                    source_credentials=credentials,
                    target_principal=service_account_email,
                    target_scopes=target_scopes,
                    lifetime=500  # seconds
                )
                
                storage_client = storage.Client(credentials=signing_credentials, project=project)
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(object_path)
                
                expiration = timedelta(minutes=expiration_minutes)
                expires_at = datetime.now(timezone.utc) + expiration
                
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=expiration,
                    method="GET",
                    service_account_email=service_account_email
                )
                
                logger.info(f"Generated signed URL (IAM) for {source_uri}, expires at {expires_at}")
                return signed_url, expires_at
            
        except Exception as e:
            logger.error(f"Error generating signed URL for {source_uri}: {e}", exc_info=True)
            return None, None
    
    @staticmethod
    def stream_from_gcs(source_uri: str):
        """
        Stream a GCS object using the default SA credentials (no signing needed).

        Args:
            source_uri: GCS URI (gs://bucket/path/to/file)

        Returns:
            Tuple of (blob_reader, content_type, size) or raises on error.
            blob_reader is a file-like object supporting .read(chunk_size).
        """
        if not source_uri or not source_uri.startswith('gs://'):
            raise ValueError(f"Invalid GCS URI: {source_uri}")

        match = re.match(r'gs://([^/]+)/(.+)', source_uri)
        if not match:
            raise ValueError(f"Cannot parse GCS URI: {source_uri}")

        bucket_name = match.group(1)
        object_path = match.group(2)

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_path)
        blob.reload()  # fetch metadata (size, content_type)

        content_type = blob.content_type or 'application/octet-stream'
        size = blob.size

        # Open as a streaming download
        reader = blob.open("rb")
        return reader, content_type, size

    @staticmethod
    def get_document_metadata(source_uri: str) -> Dict:
        """
        Extract metadata from GCS document.
        
        Args:
            source_uri: GCS URI (gs://bucket/path/to/file)
            
        Returns:
            Dictionary with file metadata (size, content_type, etc.)
        """
        if not source_uri or not source_uri.startswith('gs://'):
            return {}
        
        try:
            # Parse GCS URI
            match = re.match(r'gs://([^/]+)/(.+)', source_uri)
            if not match:
                return {}
            
            bucket_name = match.group(1)
            object_path = match.group(2)
            
            # Get blob metadata
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(object_path)
            
            # Reload to get metadata
            blob.reload()
            
            return {
                'size_bytes': blob.size,
                'content_type': blob.content_type,
                'created': str(blob.time_created) if blob.time_created else None,
                'updated': str(blob.updated) if blob.updated else None,
                'md5_hash': blob.md5_hash,
            }
            
        except Exception as e:
            logger.debug(f"Could not fetch metadata for {source_uri}: {e}")
            return {}
    
    @staticmethod
    def log_access(
        user_id: int,
        corpus_id: int,
        document_name: str,
        document_file_id: str = None,
        source_uri: str = None,
        success: bool = True,
        access_type: str = 'view',
        ip_address: str = None,
        user_agent: str = None,
        error_message: str = None
    ) -> bool:
        """
        Log document access to audit trail.
        
        Args:
            user_id: User ID accessing the document
            corpus_id: Corpus ID containing the document
            document_name: Display name of the document
            document_file_id: Vertex AI file ID (optional)
            source_uri: GCS source URI (optional)
            success: Whether access was successful
            access_type: Type of access (view, download, preview)
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)
            error_message: Error message if access failed (optional)
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO document_access_log (
                        user_id, corpus_id, document_name, document_file_id,
                        access_type, success, error_message, source_uri,
                        ip_address, user_agent, accessed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, corpus_id, document_name, document_file_id,
                    access_type, success, error_message, source_uri,
                    ip_address, user_agent, datetime.now(timezone.utc).isoformat()
                ))
                conn.commit()
                
            logger.info(
                f"Logged document access: user={user_id}, corpus={corpus_id}, "
                f"document={document_name}, success={success}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error logging document access: {e}")
            return False
    
    @staticmethod
    def get_access_logs(
        user_id: int = None,
        corpus_id: int = None,
        limit: int = 100
    ) -> list:
        """
        Retrieve document access logs with optional filters.
        
        Args:
            user_id: Filter by user ID (optional)
            corpus_id: Filter by corpus ID (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of access log records
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM document_access_log WHERE 1=1"
                params = []
                
                if user_id:
                    query += " AND user_id = %s"
                    params.append(user_id)
                
                if corpus_id:
                    query += " AND corpus_id = %s"
                    params.append(corpus_id)
                
                query += " ORDER BY accessed_at DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error retrieving access logs: {e}")
            return []
