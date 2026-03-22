"""
Tool for querying multiple Vertex AI RAG corpora simultaneously.

Since Vertex AI RAG API doesn't support multi-corpus queries in a single call,
this tool queries each corpus in parallel and merges the results with source attribution.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from google.adk.tools.tool_context import ToolContext
import vertexai
from vertexai.preview import rag
import os
from google.api_core import exceptions as google_exceptions

from rag_agent.config import PROJECT_ID, LOCATION, DEFAULT_DISTANCE_THRESHOLD, DEFAULT_TOP_K
from .utils import check_corpus_exists, get_corpus_resource_name, check_user_corpus_access

if os.getenv("VALIDATE_CORPORA_WITH_VERTEX", "true").lower() == "true":
    try:
        import google.auth
        credentials, _ = google.auth.default()
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
        print(f"DEBUG: Initialized vertexai in rag_multi_query with project={PROJECT_ID}, location={LOCATION}")
    except Exception as e:
        print(f"DEBUG: Failed to initialize vertexai in rag_multi_query: {e}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")


def _query_single_corpus(
    corpus_name: str,
    query: str,
    rag_retrieval_config: rag.RagRetrievalConfig,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Query a single corpus synchronously with retry logic.
    
    Args:
        corpus_name: Name of the corpus to query
        query: The search query
        rag_retrieval_config: Retrieval configuration
        max_retries: Maximum number of retry attempts for rate limit errors
        
    Returns:
        Dict with results or error information
    """
    corpus_resource_name = get_corpus_resource_name(corpus_name)
    
    for attempt in range(max_retries + 1):
        try:
            response = rag.retrieval_query(
                rag_resources=[
                    rag.RagResource(
                        rag_corpus=corpus_resource_name,
                    )
                ],
                text=query,
                rag_retrieval_config=rag_retrieval_config,
            )
            
            # Success - extract results and return
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
                        "corpus_source": corpus_name,
                    }
                    results.append(result)
            
            return {
                "corpus_name": corpus_name,
                "status": "success",
                "results": results,
                "error": None,
            }
            
        except google_exceptions.ResourceExhausted as e:
            # 429 RESOURCE_EXHAUSTED - retry with exponential backoff
            if attempt < max_retries:
                wait_time = (2 ** attempt) + (0.1 * attempt)  # Exponential backoff: 1s, 2.1s, 4.2s
                logging.warning(
                    f"Rate limit hit for corpus '{corpus_name}' (attempt {attempt + 1}/{max_retries + 1}). "
                    f"Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
                continue
            else:
                # Max retries exceeded
                error_msg = f"Rate limit exceeded after {max_retries + 1} attempts: {str(e)}"
                logging.error(f"Error querying corpus '{corpus_name}': {error_msg}")
                return {
                    "corpus_name": corpus_name,
                    "status": "error",
                    "results": [],
                    "error": error_msg,
                }
        
        except Exception as e:
            # Other errors - don't retry
            logging.error(f"Error querying corpus '{corpus_name}': {str(e)}")
            return {
                "corpus_name": corpus_name,
                "status": "error",
                "results": [],
                "error": str(e),
            }
    
    # Should never reach here, but just in case
    return {
        "corpus_name": corpus_name,
        "status": "error",
        "results": [],
        "error": "Unknown error: max retries logic failed",
    }


async def _query_corpus_async(
    corpus_name: str,
    query: str,
    rag_retrieval_config: rag.RagRetrievalConfig,
) -> Dict[str, Any]:
    """
    Query a single corpus asynchronously.
    
    Wraps the synchronous query in an async executor.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, 
        _query_single_corpus,
        corpus_name,
        query,
        rag_retrieval_config,
    )


def rag_multi_query(
    corpus_names: List[str],
    query: str,
    tool_context: ToolContext,
    top_k: Optional[int] = None,
) -> dict:
    """
    Query multiple Vertex AI RAG corpora in parallel and merge results.
    
    Since Vertex AI doesn't support querying multiple corpora in a single API call,
    this tool queries each corpus separately in parallel and merges the results
    with source attribution.
    
    Args:
        corpus_names: List of corpus names to query (display names or resource names)
        query: The text query to search for across all corpora
        tool_context: The tool context
        top_k: Optional number of total results to return (default: DEFAULT_TOP_K)
        
    Returns:
        dict: Combined query results with corpus source attribution
    """
    import os
    account_env = os.environ.get("ACCOUNT_ENV", "unknown")
    
    if top_k is None:
        top_k = DEFAULT_TOP_K

    if os.getenv("VALIDATE_CORPORA_WITH_VERTEX", "true").lower() != "true":
        return {
            "status": "warning",
            "message": "Vertex corpus validation is disabled; no Vertex-backed retrieval performed.",
            "query": query,
            "corpora_queried": corpus_names,
            "results": [],
            "results_count": 0,
            "results_by_corpus": {name: 0 for name in corpus_names},
        }
    
    try:
        logging.info(
            f"[{account_env}] Multi-corpus query: {len(corpus_names)} corpora, query: {query[:50]}...",
            extra={"agent": account_env, "corpora_count": len(corpus_names), "action": "rag_multi_query"}
        )
        
        if not corpus_names:
            return {
                "status": "error",
                "message": "No corpora specified. Please provide at least one corpus name.",
                "query": query,
                "corpora_queried": [],
                "results": [],
                "results_count": 0,
            }
        
        # Filter out corpora the user doesn't have access to
        authorized_corpora = []
        unauthorized_corpora_list = []
        for corpus_name in corpus_names:
            if check_user_corpus_access(corpus_name, tool_context):
                authorized_corpora.append(corpus_name)
            else:
                unauthorized_corpora_list.append(corpus_name)
        
        if unauthorized_corpora_list:
            logging.warning(
                f"[{account_env}] Corpus access denied for: {unauthorized_corpora_list}",
                extra={"agent": account_env, "unauthorized": unauthorized_corpora_list, "action": "rag_multi_query"}
            )
        
        if not authorized_corpora:
            return {
                "status": "error",
                "message": f"Access denied: you do not have permission to query any of the specified corpora. "
                           f"Your accessible corpora: {tool_context.state.get('accessible_corpus_names', [])}",
                "query": query,
                "corpora_queried": [],
                "unauthorized_corpora": unauthorized_corpora_list,
                "results": [],
                "results_count": 0,
            }
        
        validated_corpora = []
        missing_corpora = []
        
        for corpus_name in authorized_corpora:
            if check_corpus_exists(corpus_name, tool_context):
                validated_corpora.append(corpus_name)
            else:
                missing_corpora.append(corpus_name)
        
        if missing_corpora:
            logging.warning(
                f"[{account_env}] Some corpora not found: {missing_corpora}",
                extra={"agent": account_env, "missing_corpora": missing_corpora}
            )
        
        if not validated_corpora:
            return {
                "status": "error",
                "message": f"None of the specified corpora exist: {corpus_names}",
                "query": query,
                "corpora_queried": [],
                "missing_corpora": missing_corpora,
                "results": [],
                "results_count": 0,
            }
        
        rag_retrieval_config = rag.RagRetrievalConfig(
            top_k=top_k,
            filter=rag.Filter(vector_distance_threshold=DEFAULT_DISTANCE_THRESHOLD),
        )
        
        print(f"Querying {len(validated_corpora)} corpora in parallel...")
        
        # Check if there's already a running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an async context, we need to create tasks differently
            # Use run_in_executor to avoid "loop is already running" error
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(_query_single_corpus, corpus_name, query, rag_retrieval_config)
                    for corpus_name in validated_corpora
                ]
                corpus_results = [future.result() for future in futures]
        except RuntimeError:
            # No event loop running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                tasks = [
                    _query_corpus_async(corpus_name, query, rag_retrieval_config)
                    for corpus_name in validated_corpora
                ]
                corpus_results = loop.run_until_complete(asyncio.gather(*tasks))
            finally:
                loop.close()
        
        all_results = []
        failed_corpora = []
        results_by_corpus = {}
        
        for corpus_result in corpus_results:
            corpus_name = corpus_result["corpus_name"]
            
            if corpus_result["status"] == "error":
                failed_corpora.append({
                    "corpus_name": corpus_name,
                    "error": corpus_result["error"]
                })
                results_by_corpus[corpus_name] = 0
            else:
                results = corpus_result["results"]
                all_results.extend(results)
                results_by_corpus[corpus_name] = len(results)
        
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        top_results = all_results[:top_k]
        
        status = "success"
        if failed_corpora and not top_results:
            status = "error"
        elif failed_corpora:
            status = "partial_success"
        elif not top_results:
            status = "warning"
        
        message_parts = [f"Queried {len(validated_corpora)} corpora"]
        if failed_corpora:
            message_parts.append(f"{len(failed_corpora)} failed")
        if missing_corpora:
            message_parts.append(f"{len(missing_corpora)} not found")
        message = ", ".join(message_parts)
        
        logging.info(
            f"[{account_env}] Multi-corpus query complete - {len(top_results)} total results",
            extra={
                "agent": account_env,
                "corpora_count": len(validated_corpora),
                "results_count": len(top_results),
                "results_by_corpus": results_by_corpus
            }
        )
        
        response = {
            "status": status,
            "message": message,
            "query": query,
            "corpora_queried": validated_corpora,
            "results": top_results,
            "results_count": len(top_results),
            "results_by_corpus": results_by_corpus,
        }
        
        if missing_corpora:
            response["missing_corpora"] = missing_corpora
        
        if failed_corpora:
            response["failed_corpora"] = failed_corpora
        
        return response
        
    except Exception as e:
        error_msg = f"Error in multi-corpus query: {str(e)}"
        logging.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "query": query,
            "corpora_queried": corpus_names if 'corpus_names' in locals() else [],
            "results": [],
            "results_count": 0,
        }
