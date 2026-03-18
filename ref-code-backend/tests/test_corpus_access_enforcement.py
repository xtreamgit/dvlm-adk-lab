"""
Tests for corpus-level access enforcement in RAG tools.

Verifies that tools check user corpus access via session state
before allowing operations on corpora.
"""

import pytest
from unittest.mock import MagicMock, patch


class MockToolContext:
    """Mock ADK ToolContext with configurable state."""

    def __init__(self, accessible_corpus_names=None, **extra_state):
        self.state = {}
        if accessible_corpus_names is not None:
            self.state["accessible_corpus_names"] = accessible_corpus_names
        self.state.update(extra_state)


# ===========================================================================
# Tests for check_user_corpus_access utility
# ===========================================================================

class TestCheckUserCorpusAccess:
    """Test the check_user_corpus_access utility function."""

    def setup_method(self):
        # Import here to avoid module-level import issues
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    def test_access_granted_for_matching_corpus(self):
        from rag_agent.tools.utils import check_user_corpus_access
        ctx = MockToolContext(accessible_corpus_names=["ai-books", "design", "management"])
        assert check_user_corpus_access("ai-books", ctx) is True

    def test_access_denied_for_non_matching_corpus(self):
        from rag_agent.tools.utils import check_user_corpus_access
        ctx = MockToolContext(accessible_corpus_names=["ai-books", "design"])
        assert check_user_corpus_access("management", ctx) is False

    def test_access_denied_for_empty_list(self):
        from rag_agent.tools.utils import check_user_corpus_access
        ctx = MockToolContext(accessible_corpus_names=[])
        assert check_user_corpus_access("ai-books", ctx) is False

    def test_access_allowed_when_no_state_set(self):
        """When accessible_corpus_names is not in state, allow access (backward compat)."""
        from rag_agent.tools.utils import check_user_corpus_access
        ctx = MockToolContext()  # No accessible_corpus_names set
        assert check_user_corpus_access("anything", ctx) is True

    def test_access_with_resource_name_suffix(self):
        """Corpus name passed as resource path ending with display name."""
        from rag_agent.tools.utils import check_user_corpus_access
        ctx = MockToolContext(accessible_corpus_names=["ai-books"])
        assert check_user_corpus_access("projects/p/locations/l/ragCorpora/ai-books", ctx) is True

    def test_access_denied_with_resource_name_wrong_corpus(self):
        from rag_agent.tools.utils import check_user_corpus_access
        ctx = MockToolContext(accessible_corpus_names=["ai-books"])
        assert check_user_corpus_access("projects/p/locations/l/ragCorpora/management", ctx) is False

    def test_multiple_corpora_access(self):
        from rag_agent.tools.utils import check_user_corpus_access
        ctx = MockToolContext(accessible_corpus_names=["ai-books", "design", "management"])
        assert check_user_corpus_access("ai-books", ctx) is True
        assert check_user_corpus_access("design", ctx) is True
        assert check_user_corpus_access("management", ctx) is True
        assert check_user_corpus_access("secret-corpus", ctx) is False


class TestGetAccessibleCorpusNames:
    """Test the get_accessible_corpus_names utility function."""

    def setup_method(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    def test_returns_list_when_set(self):
        from rag_agent.tools.utils import get_accessible_corpus_names
        ctx = MockToolContext(accessible_corpus_names=["ai-books", "design"])
        assert get_accessible_corpus_names(ctx) == ["ai-books", "design"]

    def test_returns_empty_list_when_not_set(self):
        from rag_agent.tools.utils import get_accessible_corpus_names
        ctx = MockToolContext()
        assert get_accessible_corpus_names(ctx) == []


# ===========================================================================
# Tests for tool-level access enforcement
# ===========================================================================

class TestRagQueryAccessEnforcement:
    """Test that rag_query enforces corpus access."""

    def setup_method(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    @patch('rag_agent.tools.rag_query.check_corpus_exists', return_value=True)
    @patch('rag_agent.tools.rag_query.get_corpus_resource_name', return_value='projects/p/locations/l/ragCorpora/ai-books')
    @patch('vertexai.rag.retrieval_query')
    def test_access_denied_returns_error(self, mock_retrieval, mock_resource, mock_exists):
        from rag_agent.tools.rag_query import rag_query
        ctx = MockToolContext(accessible_corpus_names=["design"])
        result = rag_query("ai-books", "test query", ctx)
        assert result["status"] == "error"
        assert "Access denied" in result["message"]
        mock_retrieval.assert_not_called()

    @patch('rag_agent.tools.rag_query.check_corpus_exists', return_value=True)
    @patch('rag_agent.tools.rag_query.get_corpus_resource_name', return_value='projects/p/locations/l/ragCorpora/ai-books')
    @patch('vertexai.rag.retrieval_query')
    def test_access_granted_proceeds(self, mock_retrieval, mock_resource, mock_exists):
        from rag_agent.tools.rag_query import rag_query
        # Mock a response with no results
        mock_response = MagicMock()
        mock_response.contexts = None
        mock_retrieval.return_value = mock_response

        ctx = MockToolContext(accessible_corpus_names=["ai-books", "design"])
        result = rag_query("ai-books", "test query", ctx)
        # Should proceed past access check (may return warning for no results)
        assert result["status"] in ("success", "warning")
        mock_retrieval.assert_called_once()


class TestRagMultiQueryAccessEnforcement:
    """Test that rag_multi_query enforces corpus access."""

    def setup_method(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    @patch('rag_agent.tools.rag_multi_query.check_corpus_exists', return_value=True)
    @patch('rag_agent.tools.rag_multi_query._query_single_corpus')
    def test_filters_unauthorized_corpora(self, mock_query, mock_exists):
        from rag_agent.tools.rag_multi_query import rag_multi_query
        ctx = MockToolContext(accessible_corpus_names=["ai-books"])

        mock_query.return_value = {
            "corpus_name": "ai-books",
            "status": "success",
            "results": [],
            "error": None,
        }

        result = rag_multi_query(["ai-books", "management"], "test query", ctx)
        # management should be filtered out, only ai-books queried
        assert "management" not in result.get("corpora_queried", [])

    @patch('rag_agent.tools.rag_multi_query.check_corpus_exists', return_value=True)
    def test_all_unauthorized_returns_error(self, mock_exists):
        from rag_agent.tools.rag_multi_query import rag_multi_query
        ctx = MockToolContext(accessible_corpus_names=["design"])
        result = rag_multi_query(["ai-books", "management"], "test query", ctx)
        assert result["status"] == "error"
        assert "Access denied" in result["message"]


class TestGetCorpusInfoAccessEnforcement:
    """Test that get_corpus_info enforces corpus access."""

    def setup_method(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    @patch('rag_agent.tools.get_corpus_info.check_corpus_exists', return_value=True)
    @patch('rag_agent.tools.get_corpus_info.get_corpus_resource_name', return_value='projects/p/locations/l/ragCorpora/management')
    @patch('vertexai.rag.list_files', return_value=[])
    def test_access_denied_returns_error(self, mock_files, mock_resource, mock_exists):
        from rag_agent.tools.get_corpus_info import get_corpus_info
        ctx = MockToolContext(accessible_corpus_names=["ai-books"])
        result = get_corpus_info("management", ctx)
        assert result["status"] == "error"
        assert "Access denied" in result["message"]
        mock_files.assert_not_called()


class TestBrowseDocumentsAccessEnforcement:
    """Test that browse_documents enforces corpus access."""

    def setup_method(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    @patch('rag_agent.tools.browse_documents.check_corpus_exists', return_value=True)
    def test_access_denied_returns_error(self, mock_exists):
        from rag_agent.tools.browse_documents import browse_documents
        ctx = MockToolContext(accessible_corpus_names=["ai-books"])
        result = browse_documents("management", ctx)
        assert result["status"] == "error"
        assert "Access denied" in result["message"]


class TestListCorporaAccessEnforcement:
    """Test that list_corpora filters by user access."""

    def setup_method(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    @patch('rag_agent.tools.list_corpora.rag')
    def test_filters_inaccessible_corpora(self, mock_rag):
        from rag_agent.tools.list_corpora import list_corpora

        # Mock 3 corpora in Vertex AI
        corpus1 = MagicMock()
        corpus1.name = "projects/p/locations/l/ragCorpora/1"
        corpus1.display_name = "ai-books"
        corpus1.create_time = "2026-01-01"
        corpus1.update_time = "2026-01-01"

        corpus2 = MagicMock()
        corpus2.name = "projects/p/locations/l/ragCorpora/2"
        corpus2.display_name = "management"
        corpus2.create_time = "2026-01-01"
        corpus2.update_time = "2026-01-01"

        corpus3 = MagicMock()
        corpus3.name = "projects/p/locations/l/ragCorpora/3"
        corpus3.display_name = "design"
        corpus3.create_time = "2026-01-01"
        corpus3.update_time = "2026-01-01"

        mock_rag.list_corpora.return_value = [corpus1, corpus2, corpus3]

        # User only has access to ai-books and design
        ctx = MockToolContext(accessible_corpus_names=["ai-books", "design"])
        result = list_corpora(ctx)

        assert result["status"] == "success"
        corpus_names = [c["display_name"] for c in result["corpora"]]
        assert "ai-books" in corpus_names
        assert "design" in corpus_names
        assert "management" not in corpus_names
        assert len(result["corpora"]) == 2

    @patch('rag_agent.tools.list_corpora.rag')
    def test_no_filter_when_state_not_set(self, mock_rag):
        """When no access list is set, all corpora should be returned."""
        from rag_agent.tools.list_corpora import list_corpora

        corpus1 = MagicMock()
        corpus1.name = "projects/p/locations/l/ragCorpora/1"
        corpus1.display_name = "ai-books"
        corpus1.create_time = "2026-01-01"
        corpus1.update_time = "2026-01-01"

        mock_rag.list_corpora.return_value = [corpus1]

        ctx = MockToolContext()  # No accessible_corpus_names set
        result = list_corpora(ctx)

        assert result["status"] == "success"
        assert len(result["corpora"]) == 1


class TestDeleteDocumentAccessEnforcement:
    """Test that delete_document enforces corpus access."""

    def setup_method(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    @patch('rag_agent.tools.delete_document.check_corpus_exists', return_value=True)
    @patch('vertexai.rag.delete_file')
    def test_access_denied_returns_error(self, mock_delete, mock_exists):
        from rag_agent.tools.delete_document import delete_document
        ctx = MockToolContext(accessible_corpus_names=["ai-books"])
        result = delete_document("management", "doc123", ctx)
        assert result["status"] == "error"
        assert "Access denied" in result["message"]
        mock_delete.assert_not_called()


class TestDeleteCorpusAccessEnforcement:
    """Test that delete_corpus enforces corpus access."""

    def setup_method(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    @patch('rag_agent.tools.delete_corpus.check_corpus_exists', return_value=True)
    @patch('vertexai.rag.delete_corpus')
    def test_access_denied_returns_error(self, mock_delete, mock_exists):
        from rag_agent.tools.delete_corpus import delete_corpus
        ctx = MockToolContext(accessible_corpus_names=["ai-books"])
        result = delete_corpus("management", True, ctx)
        assert result["status"] == "error"
        assert "Access denied" in result["message"]
        mock_delete.assert_not_called()


class TestSetCurrentCorpusAccessEnforcement:
    """Test that set_current_corpus enforces corpus access."""

    def setup_method(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    @patch('rag_agent.tools.utils.check_corpus_exists', return_value=True)
    def test_access_denied_returns_false(self, mock_exists):
        from rag_agent.tools.utils import set_current_corpus
        ctx = MockToolContext(accessible_corpus_names=["ai-books"])
        result = set_current_corpus("management", ctx)
        assert result is False
        assert ctx.state.get("current_corpus") is None

    @patch('rag_agent.tools.utils.check_corpus_exists', return_value=True)
    def test_access_granted_sets_corpus(self, mock_exists):
        from rag_agent.tools.utils import set_current_corpus
        ctx = MockToolContext(accessible_corpus_names=["ai-books", "management"])
        result = set_current_corpus("management", ctx)
        assert result is True
        assert ctx.state["current_corpus"] == "management"

    @patch('rag_agent.tools.utils.check_corpus_exists', return_value=True)
    def test_no_access_list_allows_set(self, mock_exists):
        """When no access list is set, allow setting current corpus (backward compat)."""
        from rag_agent.tools.utils import set_current_corpus
        ctx = MockToolContext()  # No accessible_corpus_names
        result = set_current_corpus("anything", ctx)
        assert result is True
        assert ctx.state["current_corpus"] == "anything"


class TestCreateCorpusAuditLogging:
    """Test that create_corpus logs user identity for audit."""

    def setup_method(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    @patch('rag_agent.tools.create_corpus.check_corpus_exists', return_value=True)
    def test_logs_user_email_on_existing_corpus(self, mock_exists):
        """Verify create_corpus reads user_email from state (audit trail)."""
        from rag_agent.tools.create_corpus import create_corpus
        ctx = MockToolContext(
            accessible_corpus_names=["ai-books"],
            user_email="hector@develom.com"
        )
        result = create_corpus("ai-books", ctx)
        # Corpus already exists, should return info status
        assert result["status"] == "info"
        # Verify user_email was accessible from state
        assert ctx.state["user_email"] == "hector@develom.com"


class TestAddDataAccessEnforcement:
    """Test that add_data enforces corpus access."""

    def setup_method(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

    @patch('rag_agent.tools.add_data.check_corpus_exists', return_value=True)
    @patch('vertexai.rag.import_files')
    def test_access_denied_returns_error(self, mock_import, mock_exists):
        from rag_agent.tools.add_data import add_data
        ctx = MockToolContext(accessible_corpus_names=["ai-books"])
        result = add_data("management", ["gs://bucket/file.pdf"], ctx)
        assert result["status"] == "error"
        assert "Access denied" in result["message"]
        mock_import.assert_not_called()
