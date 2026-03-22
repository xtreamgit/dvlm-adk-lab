"""
Corpus synchronization service for Vertex AI RAG.
Keeps database in sync with Vertex AI as source of truth.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def _update_corpus_document_count(corpus_id: int, file_count: int) -> None:
    """Update document count in corpus_metadata for a given corpus."""
    try:
        from database.repositories.corpus_metadata_repository import CorpusMetadataRepository
        # Ensure metadata row exists
        CorpusMetadataRepository.ensure_exists(corpus_id)
        # Update document count
        CorpusMetadataRepository.update_document_count(corpus_id, file_count)
        logger.debug(f"Updated document_count={file_count} for corpus_id={corpus_id}")
    except Exception as e:
        logger.warning(f"Could not update document count for corpus {corpus_id}: {e}")


class CorpusSyncService:
    """Service for synchronizing corpora from Vertex AI to database."""
    
    @staticmethod
    def sync_from_vertex(project_id: str, location: str) -> Dict[str, Any]:
        """
        Sync corpora from Vertex AI to database.
        
        Args:
            project_id: GCP project ID
            location: GCP location/region
            
        Returns:
            Dict with sync results (added, updated, deactivated counts, errors)
        """
        result = {
            'status': 'success',
            'added': 0,
            'updated': 0,
            'deactivated': 0,
            'errors': [],
            'vertex_count': 0,
            'db_active_count': 0
        }

        if os.getenv("VALIDATE_CORPORA_WITH_VERTEX", "true").lower() != "true":
            result['status'] = 'skipped'
            return result
        
        try:
            # Import dependencies
            import vertexai
            from vertexai import rag
            import google.auth
            from database.repositories.corpus_repository import CorpusRepository
            
            # Initialize Vertex AI
            try:
                credentials, _ = google.auth.default()
                vertexai.init(project=project_id, location=location, credentials=credentials)
                logger.info(f"Vertex AI initialized for project={project_id}, location={location}")
            except Exception as e:
                error_msg = f"Failed to initialize Vertex AI: {e}"
                logger.error(error_msg)
                result['status'] = 'error'
                result['errors'].append(error_msg)
                return result
            
            # Fetch corpora from Vertex AI
            try:
                vertex_corpora = list(rag.list_corpora())
                vertex_corpus_dict = {}
                
                logger.info(f"Found {len(vertex_corpora)} corpora in Vertex AI")
                
                for corpus in vertex_corpora:
                    display_name = corpus.display_name
                    resource_name = corpus.name
                    
                    # Try to get GCS bucket and file count from corpus files
                    gcs_bucket = None
                    files = []
                    try:
                        files = list(rag.list_files(corpus.name))
                        if files:
                            # Extract bucket from first file URI
                            # Format: gs://bucket-name/path/to/file.pdf
                            first_file_uri = files[0].name if hasattr(files[0], 'name') else str(files[0])
                            if first_file_uri.startswith('gs://'):
                                bucket_name = first_file_uri.split('/')[2]
                                gcs_bucket = f"gs://{bucket_name}"
                    except Exception as e:
                        logger.debug(f"Could not fetch files for corpus {display_name}: {e}")
                    
                    # Fallback to default bucket naming if we couldn't get it from files
                    if not gcs_bucket:
                        gcs_bucket = f"gs://{project_id}-{display_name}"
                    
                    vertex_corpus_dict[display_name] = {
                        'resource_name': resource_name,
                        'display_name': display_name,
                        'create_time': corpus.create_time,
                        'gcs_bucket': gcs_bucket,
                        'file_count': len(files) if files else 0
                    }
                    
                    logger.debug(f"Vertex corpus: {display_name} -> {resource_name}")
                
                result['vertex_count'] = len(vertex_corpora)
                
            except Exception as e:
                error_msg = f"Failed to fetch corpora from Vertex AI: {e}"
                logger.error(error_msg)
                result['status'] = 'error'
                result['errors'].append(error_msg)
                return result
            
            # Fetch corpora from database
            try:
                db_corpora = CorpusRepository.get_all(active_only=False)
                db_corpus_dict = {c['name']: c for c in db_corpora}
                
                logger.info(f"Found {len(db_corpora)} corpora in database")
                
            except Exception as e:
                error_msg = f"Failed to fetch corpora from database: {e}"
                logger.error(error_msg)
                result['status'] = 'error'
                result['errors'].append(error_msg)
                return result
            
            # Sync logic
            vertex_names = set(vertex_corpus_dict.keys())
            db_names = set(db_corpus_dict.keys())
            
            # Corpora to add (in Vertex AI but not in DB)
            to_add = vertex_names - db_names
            
            # Corpora to deactivate (in DB but not in Vertex AI)
            to_deactivate = db_names - vertex_names
            
            # Corpora to reactivate/update (in both)
            to_update = vertex_names & db_names
            
            logger.info(f"Sync analysis: add={len(to_add)}, deactivate={len(to_deactivate)}, update={len(to_update)}")
            
            # Add new corpora
            if to_add:
                logger.info(f"Adding {len(to_add)} new corpora")
                for corpus_name in to_add:
                    vertex_corpus = vertex_corpus_dict[corpus_name]
                    try:
                        # Create corpus in database
                        corpus_dict = CorpusRepository.create(
                            name=corpus_name,
                            display_name=corpus_name,
                            gcs_bucket=vertex_corpus['gcs_bucket'],
                            description=f"Auto-synced from Vertex AI on {datetime.now().isoformat()}",
                            vertex_corpus_id=vertex_corpus['resource_name']
                        )
                        
                        logger.info(f"Added corpus: {corpus_name} (ID: {corpus_dict['id']})")
                        result['added'] += 1
                        
                        # Update document count in metadata
                        _update_corpus_document_count(
                            corpus_dict['id'],
                            vertex_corpus['file_count']
                        )
                        
                        # Note: Legacy GroupRepository removed. Default group access is now
                        # managed via Google Groups Bridge (chatbot_groups / chatbot_corpus_access).
                            
                    except Exception as e:
                        error_msg = f"Failed to add corpus {corpus_name}: {e}"
                        logger.error(error_msg)
                        result['errors'].append(error_msg)
            
            # Deactivate removed corpora
            if to_deactivate:
                logger.info(f"Deactivating {len(to_deactivate)} removed corpora")
                for corpus_name in to_deactivate:
                    db_corpus = db_corpus_dict[corpus_name]
                    if db_corpus['is_active']:
                        try:
                            CorpusRepository.update(
                                corpus_id=db_corpus['id'],
                                is_active=False
                            )
                            logger.info(f"Deactivated corpus: {corpus_name}")
                            result['deactivated'] += 1
                        except Exception as e:
                            error_msg = f"Failed to deactivate corpus {corpus_name}: {e}"
                            logger.error(error_msg)
                            result['errors'].append(error_msg)
                    else:
                        logger.debug(f"Corpus already inactive: {corpus_name}")
            
            # Update/reactivate existing corpora
            if to_update:
                logger.info(f"Updating {len(to_update)} existing corpora")
                for corpus_name in to_update:
                    db_corpus = db_corpus_dict[corpus_name]
                    vertex_corpus = vertex_corpus_dict[corpus_name]
                    
                    updates = {}
                    
                    # Reactivate if inactive
                    if not db_corpus['is_active']:
                        updates['is_active'] = True
                    
                    # Update vertex_corpus_id if different
                    if db_corpus['vertex_corpus_id'] != vertex_corpus['resource_name']:
                        updates['vertex_corpus_id'] = vertex_corpus['resource_name']
                    
                    # Update GCS bucket if different
                    if db_corpus['gcs_bucket'] != vertex_corpus['gcs_bucket']:
                        updates['gcs_bucket'] = vertex_corpus['gcs_bucket']
                    
                    if updates:
                        try:
                            CorpusRepository.update(
                                corpus_id=db_corpus['id'],
                                **updates
                            )
                            update_desc = ', '.join([f"{k}={v}" for k, v in updates.items()])
                            logger.info(f"Updated corpus: {corpus_name} ({update_desc})")
                            result['updated'] += 1
                        except Exception as e:
                            error_msg = f"Failed to update corpus {corpus_name}: {e}"
                            logger.error(error_msg)
                            result['errors'].append(error_msg)
                    else:
                        logger.debug(f"No changes needed for corpus: {corpus_name}")
                    
                    # Always update document count (even if no other changes)
                    _update_corpus_document_count(
                        db_corpus['id'],
                        vertex_corpus['file_count']
                    )
            
            # Final count
            try:
                active_corpora = CorpusRepository.get_all(active_only=True)
                result['db_active_count'] = len(active_corpora)
            except Exception as e:
                logger.warning(f"Could not get final active corpus count: {e}")
            
            # Set status based on errors
            if result['errors']:
                result['status'] = 'partial' if (result['added'] + result['updated'] + result['deactivated']) > 0 else 'error'
            
            logger.info(f"Sync completed: status={result['status']}, added={result['added']}, "
                       f"updated={result['updated']}, deactivated={result['deactivated']}, "
                       f"errors={len(result['errors'])}")
            
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error during sync: {e}"
            logger.error(error_msg, exc_info=True)
            result['status'] = 'error'
            result['errors'].append(error_msg)
            return result
    
    @staticmethod
    def sync_on_startup(project_id: str, location: str) -> None:
        """
        Run sync on application startup.
        Logs errors but doesn't crash the app.
        
        Args:
            project_id: GCP project ID
            location: GCP location/region
        """
        logger.info("=" * 70)
        logger.info("Starting Vertex AI corpus synchronization on startup...")
        logger.info("=" * 70)

        if os.getenv("VALIDATE_CORPORA_WITH_VERTEX", "true").lower() != "true":
            logger.info("Vertex corpus sync skipped because VALIDATE_CORPORA_WITH_VERTEX=false")
            logger.info("=" * 70)
            return
        
        try:
            result = CorpusSyncService.sync_from_vertex(project_id, location)
            
            if result['status'] == 'success':
                logger.info("✅ Corpus sync completed successfully")
                logger.info(f"   Vertex AI corpora: {result['vertex_count']}")
                logger.info(f"   Database active corpora: {result['db_active_count']}")
                logger.info(f"   Added: {result['added']}, Updated: {result['updated']}, Deactivated: {result['deactivated']}")
            elif result['status'] == 'partial':
                logger.warning("⚠️  Corpus sync completed with errors")
                logger.warning(f"   Added: {result['added']}, Updated: {result['updated']}, Deactivated: {result['deactivated']}")
                logger.warning(f"   Errors: {len(result['errors'])}")
                for error in result['errors']:
                    logger.warning(f"     - {error}")
            else:
                logger.error("❌ Corpus sync failed")
                for error in result['errors']:
                    logger.error(f"   - {error}")
                logger.error("   Application will continue with existing database data")
                
        except Exception as e:
            logger.error(f"❌ Unexpected error during startup sync: {e}", exc_info=True)
            logger.error("   Application will continue with existing database data")
        
        logger.info("=" * 70)
