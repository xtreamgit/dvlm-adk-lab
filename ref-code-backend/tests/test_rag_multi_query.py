"""
Unit tests for rag_multi_query tool - multi-corpus RAG queries.
Tests parallel execution, result merging, and error handling.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any


@pytest.fixture
def mock_tool_context():
    """Mock ToolContext for testing."""
    context = Mock()
    context.state = {}
    return context


@pytest.fixture
def mock_rag_config():
    """Mock RagRetrievalConfig."""
    with patch('backend.src.rag_agent.tools.rag_multi_query.rag') as mock_rag:
        mock_config = Mock()
        mock_rag.RagRetrievalConfig.return_value = mock_config
        mock_rag.Filter.return_value = Mock()
        yield mock_rag


@pytest.fixture
def sample_corpus_results():
    """Sample corpus query results for testing."""
    return {
        "corpus1": [
            {
                "source_uri": "gs://bucket/doc1.pdf",
                "source_name": "Document 1",
                "text": "This is content from corpus1",
                "score": 0.95,
                "corpus_source": "corpus1"
            },
            {
                "source_uri": "gs://bucket/doc2.pdf",
                "source_name": "Document 2",
                "text": "More content from corpus1",
                "score": 0.85,
                "corpus_source": "corpus1"
            }
        ],
        "corpus2": [
            {
                "source_uri": "gs://bucket2/doc3.pdf",
                "source_name": "Document 3",
                "text": "This is content from corpus2",
                "score": 0.92,
                "corpus_source": "corpus2"
            }
        ],
        "corpus3": [
            {
                "source_uri": "gs://bucket3/doc4.pdf",
                "source_name": "Document 4",
                "text": "This is content from corpus3",
                "score": 0.88,
                "corpus_source": "corpus3"
            }
        ]
    }


class TestRagMultiQueryUnit:
    """Unit tests for rag_multi_query function."""
    
    @pytest.mark.unit
    def test_empty_corpus_list_returns_error(self, mock_tool_context):
        """Test that empty corpus list returns appropriate error."""
        from src.rag_agent.tools.rag_multi_query import rag_multi_query
        
        result = rag_multi_query(
            corpus_names=[],
            query="test query",
            tool_context=mock_tool_context
        )
        
        assert result["status"] == "error"
        assert "No corpora specified" in result["message"]
        assert result["results_count"] == 0
    
    @pytest.mark.unit
    @patch('src.rag_agent.tools.rag_multi_query.check_corpus_exists')
    def test_missing_corpora_returns_error(self, mock_check, mock_tool_context):
        """Test that all missing corpora returns error."""
        mock_check.return_value = False
        
        from src.rag_agent.tools.rag_multi_query import rag_multi_query
        
        result = rag_multi_query(
            corpus_names=["missing1", "missing2"],
            query="test query",
            tool_context=mock_tool_context
        )
        
        assert result["status"] == "error"
        assert "None of the specified corpora exist" in result["message"]
        assert result["missing_corpora"] == ["missing1", "missing2"]
    
    @pytest.mark.unit
    @patch('src.rag_agent.tools.rag_multi_query.check_corpus_exists')
    @patch('src.rag_agent.tools.rag_multi_query.get_corpus_resource_name')
    @patch('src.rag_agent.tools.rag_multi_query.rag')
    @patch('src.rag_agent.tools.rag_multi_query.asyncio')
    def test_successful_single_corpus_query(
        self, mock_asyncio, mock_rag, mock_get_name, mock_check, mock_tool_context
    ):
        """Test successful query of single corpus."""
        # Setup mocks
        mock_check.return_value = True
        mock_get_name.return_value = "projects/test/locations/us-west1/ragCorpora/corpus1"
        
        # Mock response
        mock_ctx = Mock()
        mock_ctx.source_uri = "gs://test/doc1.pdf"
        mock_ctx.source_display_name = "Doc 1"
        mock_ctx.text = "Test content"
        mock_ctx.score = 0.95
        
        mock_response = Mock()
        mock_response.contexts = Mock()
        mock_response.contexts.contexts = [mock_ctx]
        
        mock_rag.retrieval_query.return_value = mock_response
        mock_rag.RagRetrievalConfig.return_value = Mock()
        mock_rag.Filter.return_value = Mock()
        mock_rag.RagResource.return_value = Mock()
        
        # Mock asyncio
        mock_loop = Mock()
        mock_loop.run_until_complete.return_value = [
            {
                "corpus_name": "corpus1",
                "status": "success",
                "results": [{
                    "source_uri": "gs://test/doc1.pdf",
                    "source_name": "Doc 1",
                    "text": "Test content",
                    "score": 0.95,
                    "corpus_source": "corpus1"
                }],
                "error": None
            }
        ]
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_asyncio.set_event_loop.return_value = None
        
        from src.rag_agent.tools.rag_multi_query import rag_multi_query
        
        result = rag_multi_query(
            corpus_names=["corpus1"],
            query="test query",
            tool_context=mock_tool_context
        )
        
        assert result["status"] == "success"
        assert result["results_count"] == 1
        assert result["corpora_queried"] == ["corpus1"]
        assert result["results"][0]["corpus_source"] == "corpus1"
    
    @pytest.mark.unit
    @patch('src.rag_agent.tools.rag_multi_query.check_corpus_exists')
    @patch('src.rag_agent.tools.rag_multi_query.get_corpus_resource_name')
    @patch('src.rag_agent.tools.rag_multi_query.rag')
    @patch('src.rag_agent.tools.rag_multi_query.asyncio')
    def test_successful_multi_corpus_query(
        self, mock_asyncio, mock_rag, mock_get_name, mock_check, 
        mock_tool_context, sample_corpus_results
    ):
        """Test successful query of multiple corpora with result merging."""
        mock_check.return_value = True
        mock_get_name.side_effect = lambda x: f"projects/test/locations/us-west1/ragCorpora/{x}"
        
        # Mock asyncio to return results from 3 corpora
        mock_loop = Mock()
        mock_loop.run_until_complete.return_value = [
            {
                "corpus_name": "corpus1",
                "status": "success",
                "results": sample_corpus_results["corpus1"],
                "error": None
            },
            {
                "corpus_name": "corpus2",
                "status": "success",
                "results": sample_corpus_results["corpus2"],
                "error": None
            },
            {
                "corpus_name": "corpus3",
                "status": "success",
                "results": sample_corpus_results["corpus3"],
                "error": None
            }
        ]
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_asyncio.set_event_loop.return_value = None
        
        mock_rag.RagRetrievalConfig.return_value = Mock()
        mock_rag.Filter.return_value = Mock()
        
        from src.rag_agent.tools.rag_multi_query import rag_multi_query
        
        result = rag_multi_query(
            corpus_names=["corpus1", "corpus2", "corpus3"],
            query="test query",
            tool_context=mock_tool_context,
            top_k=10  # Use higher top_k to get all results
        )
        
        assert result["status"] == "success"
        assert result["results_count"] == 4  # 2 + 1 + 1
        assert result["corpora_queried"] == ["corpus1", "corpus2", "corpus3"]
        
        # Verify results are sorted by score (descending)
        scores = [r["score"] for r in result["results"]]
        assert scores == sorted(scores, reverse=True)
        
        # Verify all results have corpus_source
        for r in result["results"]:
            assert "corpus_source" in r
            assert r["corpus_source"] in ["corpus1", "corpus2", "corpus3"]
        
        # Verify results_by_corpus breakdown
        assert result["results_by_corpus"]["corpus1"] == 2
        assert result["results_by_corpus"]["corpus2"] == 1
        assert result["results_by_corpus"]["corpus3"] == 1
    
    @pytest.mark.unit
    @patch('src.rag_agent.tools.rag_multi_query.check_corpus_exists')
    @patch('src.rag_agent.tools.rag_multi_query.get_corpus_resource_name')
    @patch('src.rag_agent.tools.rag_multi_query.rag')
    @patch('src.rag_agent.tools.rag_multi_query.asyncio')
    def test_partial_success_with_failed_corpus(
        self, mock_asyncio, mock_rag, mock_get_name, mock_check, 
        mock_tool_context, sample_corpus_results
    ):
        """Test that query succeeds even if one corpus fails."""
        mock_check.return_value = True
        mock_get_name.side_effect = lambda x: f"projects/test/locations/us-west1/ragCorpora/{x}"
        
        # Mock asyncio - corpus2 fails, others succeed
        mock_loop = Mock()
        mock_loop.run_until_complete.return_value = [
            {
                "corpus_name": "corpus1",
                "status": "success",
                "results": sample_corpus_results["corpus1"],
                "error": None
            },
            {
                "corpus_name": "corpus2",
                "status": "error",
                "results": [],
                "error": "Query timeout"
            },
            {
                "corpus_name": "corpus3",
                "status": "success",
                "results": sample_corpus_results["corpus3"],
                "error": None
            }
        ]
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_asyncio.set_event_loop.return_value = None
        
        mock_rag.RagRetrievalConfig.return_value = Mock()
        mock_rag.Filter.return_value = Mock()
        
        from src.rag_agent.tools.rag_multi_query import rag_multi_query
        
        result = rag_multi_query(
            corpus_names=["corpus1", "corpus2", "corpus3"],
            query="test query",
            tool_context=mock_tool_context
        )
        
        assert result["status"] == "partial_success"
        assert result["results_count"] == 3  # 2 + 0 + 1
        assert len(result["failed_corpora"]) == 1
        assert result["failed_corpora"][0]["corpus_name"] == "corpus2"
        assert "Query timeout" in result["failed_corpora"][0]["error"]
        
        # Should still have results from successful corpora
        corpus_sources = {r["corpus_source"] for r in result["results"]}
        assert "corpus1" in corpus_sources
        assert "corpus3" in corpus_sources
        assert "corpus2" not in corpus_sources
    
    @pytest.mark.unit
    @patch('src.rag_agent.tools.rag_multi_query.check_corpus_exists')
    @patch('src.rag_agent.tools.rag_multi_query.get_corpus_resource_name')
    @patch('src.rag_agent.tools.rag_multi_query.rag')
    @patch('src.rag_agent.tools.rag_multi_query.asyncio')
    def test_some_corpora_missing(
        self, mock_asyncio, mock_rag, mock_get_name, mock_check, 
        mock_tool_context, sample_corpus_results
    ):
        """Test query when some corpora don't exist."""
        # corpus1 exists, corpus2 missing, corpus3 exists
        def check_exists(corpus_name, ctx):
            return corpus_name in ["corpus1", "corpus3"]
        
        mock_check.side_effect = check_exists
        mock_get_name.side_effect = lambda x: f"projects/test/locations/us-west1/ragCorpora/{x}"
        
        # Mock asyncio - only corpus1 and corpus3
        mock_loop = Mock()
        mock_loop.run_until_complete.return_value = [
            {
                "corpus_name": "corpus1",
                "status": "success",
                "results": sample_corpus_results["corpus1"],
                "error": None
            },
            {
                "corpus_name": "corpus3",
                "status": "success",
                "results": sample_corpus_results["corpus3"],
                "error": None
            }
        ]
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_asyncio.set_event_loop.return_value = None
        
        mock_rag.RagRetrievalConfig.return_value = Mock()
        mock_rag.Filter.return_value = Mock()
        
        from src.rag_agent.tools.rag_multi_query import rag_multi_query
        
        result = rag_multi_query(
            corpus_names=["corpus1", "corpus2", "corpus3"],
            query="test query",
            tool_context=mock_tool_context
        )
        
        assert result["status"] == "success"
        assert result["corpora_queried"] == ["corpus1", "corpus3"]
        assert result["missing_corpora"] == ["corpus2"]
        assert result["results_count"] == 3  # 2 + 1
    
    @pytest.mark.unit
    @patch('src.rag_agent.tools.rag_multi_query.check_corpus_exists')
    @patch('src.rag_agent.tools.rag_multi_query.get_corpus_resource_name')
    @patch('src.rag_agent.tools.rag_multi_query.rag')
    @patch('src.rag_agent.tools.rag_multi_query.asyncio')
    def test_custom_top_k_limits_results(
        self, mock_asyncio, mock_rag, mock_get_name, mock_check, 
        mock_tool_context, sample_corpus_results
    ):
        """Test that top_k parameter limits total results."""
        mock_check.return_value = True
        mock_get_name.side_effect = lambda x: f"projects/test/locations/us-west1/ragCorpora/{x}"
        
        # Mock asyncio with 4 total results
        mock_loop = Mock()
        mock_loop.run_until_complete.return_value = [
            {
                "corpus_name": "corpus1",
                "status": "success",
                "results": sample_corpus_results["corpus1"],  # 2 results
                "error": None
            },
            {
                "corpus_name": "corpus2",
                "status": "success",
                "results": sample_corpus_results["corpus2"],  # 1 result
                "error": None
            },
            {
                "corpus_name": "corpus3",
                "status": "success",
                "results": sample_corpus_results["corpus3"],  # 1 result
                "error": None
            }
        ]
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_asyncio.set_event_loop.return_value = None
        
        mock_rag.RagRetrievalConfig.return_value = Mock()
        mock_rag.Filter.return_value = Mock()
        
        from src.rag_agent.tools.rag_multi_query import rag_multi_query
        
        result = rag_multi_query(
            corpus_names=["corpus1", "corpus2", "corpus3"],
            query="test query",
            tool_context=mock_tool_context,
            top_k=2  # Limit to 2 results
        )
        
        assert result["status"] == "success"
        assert result["results_count"] == 2  # Limited by top_k
        
        # Should return highest scoring results
        assert all(r["score"] >= 0.92 for r in result["results"])


class TestRagMultiQueryResultMerging:
    """Tests for result merging and sorting logic."""
    
    @pytest.mark.unit
    def test_results_sorted_by_score_descending(self):
        """Test that merged results are sorted by score (highest first)."""
        # This is tested implicitly in test_successful_multi_corpus_query
        # but we can add explicit verification here if needed
        pass
    
    @pytest.mark.unit
    def test_corpus_source_attribution_preserved(self):
        """Test that each result maintains corpus_source field."""
        # This is tested implicitly in test_successful_multi_corpus_query
        pass


class TestRagMultiQueryErrorHandling:
    """Tests for error handling and edge cases."""
    
    @pytest.mark.unit
    @patch('src.rag_agent.tools.rag_multi_query.check_corpus_exists')
    @patch('src.rag_agent.tools.rag_multi_query.get_corpus_resource_name')
    @patch('src.rag_agent.tools.rag_multi_query.rag')
    @patch('src.rag_agent.tools.rag_multi_query.asyncio')
    def test_all_corpora_return_no_results(
        self, mock_asyncio, mock_rag, mock_get_name, mock_check, mock_tool_context
    ):
        """Test when all corpora return 0 results."""
        mock_check.return_value = True
        mock_get_name.side_effect = lambda x: f"projects/test/locations/us-west1/ragCorpora/{x}"
        
        # All corpora return empty results
        mock_loop = Mock()
        mock_loop.run_until_complete.return_value = [
            {"corpus_name": "corpus1", "status": "success", "results": [], "error": None},
            {"corpus_name": "corpus2", "status": "success", "results": [], "error": None}
        ]
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_asyncio.set_event_loop.return_value = None
        
        mock_rag.RagRetrievalConfig.return_value = Mock()
        mock_rag.Filter.return_value = Mock()
        
        from src.rag_agent.tools.rag_multi_query import rag_multi_query
        
        result = rag_multi_query(
            corpus_names=["corpus1", "corpus2"],
            query="test query",
            tool_context=mock_tool_context
        )
        
        assert result["status"] == "warning"
        assert result["results_count"] == 0
        assert result["corpora_queried"] == ["corpus1", "corpus2"]
    
    @pytest.mark.unit
    @patch('src.rag_agent.tools.rag_multi_query.check_corpus_exists')
    def test_exception_handling(self, mock_check, mock_tool_context):
        """Test that exceptions are caught and returned as errors."""
        mock_check.side_effect = Exception("Unexpected error")
        
        from src.rag_agent.tools.rag_multi_query import rag_multi_query
        
        result = rag_multi_query(
            corpus_names=["corpus1"],
            query="test query",
            tool_context=mock_tool_context
        )
        
        assert result["status"] == "error"
        assert "Error in multi-corpus query" in result["message"]


class TestRagMultiQueryPerformance:
    """Performance-related tests (marked as @pytest.mark.performance)."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_parallel_execution_faster_than_sequential(self):
        """
        Test that parallel execution is faster than sequential.
        This would require actual corpus setup - marked as slow test.
        """
        # This test would need real corpora and would be slow
        # Placeholder for when we do performance testing
        pytest.skip("Requires real corpus setup and is slow")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
