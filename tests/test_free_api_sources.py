"""Tests for Free API Clients - Task 1.4.

Tests for Task 1.4: 無料API統合
"""

import time
from unittest.mock import MagicMock, patch


class TestPubMedClientNew:
    """Tests for PubMed client."""

    def test_client_init(self):
        """Test client initialization."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        client = PubMedClient(
            email="test@example.com",
            tool_name="test-tool",
        )
        assert client.email == "test@example.com"

    def test_pubmed_article_dataclass(self):
        """Test PubMedArticle dataclass."""
        from jarvis_core.sources.pubmed_client import PubMedArticle

        article = PubMedArticle(
            pmid="12345678",
            title="Test Article",
            abstract="This is an abstract.",
            authors=["Smith J", "Doe J"],
        )

        assert article.pmid == "12345678"
        assert len(article.authors) == 2

        d = article.to_dict()
        assert d["pmid"] == "12345678"

    def test_rate_limit_wait(self):
        """Test rate limiting."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        client = PubMedClient(rate_limit=0.1)

        start = time.time()
        client._rate_limit_wait()
        client._rate_limit_wait()
        elapsed = time.time() - start

        assert elapsed >= 0.1

    def test_search_mock(self):
        """Test search with mocked response."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        client = PubMedClient()

        with patch.object(client._session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"esearchresult": {"idlist": ["123", "456"]}}
            mock_get.return_value = mock_response

            result = client.search("test query")
            assert result == ["123", "456"]


class TestSemanticScholarClientNew:
    """Tests for Semantic Scholar client."""

    def test_client_init(self):
        """Test client initialization."""
        from jarvis_core.sources.semantic_scholar_client import SemanticScholarClient

        client = SemanticScholarClient()
        assert client.rate_limit == 3.0

    def test_s2_paper_dataclass(self):
        """Test S2Paper dataclass."""
        from jarvis_core.sources.semantic_scholar_client import S2Author, S2Paper

        paper = S2Paper(
            paper_id="abc123",
            title="Test Paper",
            authors=[S2Author("a1", "John Doe")],
            year=2024,
            citation_count=100,
        )

        assert paper.citation_count == 100
        d = paper.to_dict()
        assert d["year"] == 2024

    def test_search_mock(self):
        """Test search with mocked response."""
        from jarvis_core.sources.semantic_scholar_client import SemanticScholarClient

        client = SemanticScholarClient()

        with patch.object(client._session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [
                    {
                        "paperId": "abc",
                        "title": "Test",
                        "authors": [],
                    }
                ]
            }
            mock_get.return_value = mock_response

            results = client.search("machine learning")
            assert len(results) == 1
            assert results[0].paper_id == "abc"


class TestOpenAlexClientNew:
    """Tests for OpenAlex client."""

    def test_client_init(self):
        """Test client initialization."""
        from jarvis_core.sources.openalex_client import OpenAlexClient

        client = OpenAlexClient(email="test@example.com")
        assert client.email == "test@example.com"

    def test_openalex_work_dataclass(self):
        """Test OpenAlexWork dataclass."""
        from jarvis_core.sources.openalex_client import OpenAlexWork

        work = OpenAlexWork(
            openalex_id="W123",
            title="Test Work",
            publication_year=2024,
            cited_by_count=50,
        )

        assert work.cited_by_count == 50
        d = work.to_dict()
        assert d["publication_year"] == 2024

    def test_search_mock(self):
        """Test search with mocked response."""
        from jarvis_core.sources.openalex_client import OpenAlexClient

        client = OpenAlexClient()

        with patch.object(client._session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "results": [
                    {
                        "id": "https://openalex.org/W123",
                        "title": "Test",
                        "authorships": [],
                    }
                ]
            }
            mock_get.return_value = mock_response

            results = client.search("deep learning")
            assert len(results) == 1
            assert results[0].openalex_id == "W123"


class TestUnifiedSourceClientNew:
    """Tests for Unified Source Client."""

    def test_client_init(self):
        """Test client initialization."""
        from jarvis_core.sources.unified_source_client import UnifiedSourceClient

        client = UnifiedSourceClient(email="test@example.com")
        assert client.pubmed is not None
        assert client.s2 is not None
        assert client.openalex is not None

    def test_unified_paper_from_pubmed(self):
        """Test UnifiedPaper creation from PubMed."""
        from jarvis_core.sources.pubmed_client import PubMedArticle
        from jarvis_core.sources.unified_source_client import SourceType, UnifiedPaper

        article = PubMedArticle(
            pmid="12345",
            title="Test",
            pub_date="2024-01",
        )

        paper = UnifiedPaper.from_pubmed(article)
        assert paper.source == SourceType.PUBMED
        assert paper.id == "pubmed:12345"
        assert paper.year == 2024

    def test_unified_paper_from_s2(self):
        """Test UnifiedPaper creation from Semantic Scholar."""
        from jarvis_core.sources.semantic_scholar_client import S2Paper
        from jarvis_core.sources.unified_source_client import SourceType, UnifiedPaper

        s2paper = S2Paper(
            paper_id="abc123",
            title="Test",
            year=2023,
        )

        paper = UnifiedPaper.from_s2(s2paper)
        assert paper.source == SourceType.SEMANTIC_SCHOLAR
        assert paper.year == 2023

    def test_unified_paper_from_openalex(self):
        """Test UnifiedPaper creation from OpenAlex."""
        from jarvis_core.sources.openalex_client import OpenAlexWork
        from jarvis_core.sources.unified_source_client import SourceType, UnifiedPaper

        work = OpenAlexWork(
            openalex_id="W123",
            title="Test",
            publication_year=2022,
        )

        paper = UnifiedPaper.from_openalex(work)
        assert paper.source == SourceType.OPENALEX
        assert paper.year == 2022

    def test_deduplicate(self):
        """Test deduplication by DOI."""
        from jarvis_core.sources.unified_source_client import (
            SourceType,
            UnifiedPaper,
            UnifiedSourceClient,
        )

        client = UnifiedSourceClient()

        papers = [
            UnifiedPaper(id="1", source=SourceType.PUBMED, title="A", doi="10.1/a"),
            UnifiedPaper(id="2", source=SourceType.OPENALEX, title="A", doi="10.1/a"),
            UnifiedPaper(id="3", source=SourceType.PUBMED, title="B", doi="10.1/b"),
        ]

        deduped = client._deduplicate(papers)
        assert len(deduped) == 2

    def test_status(self):
        """Test status report."""
        from jarvis_core.sources.unified_source_client import UnifiedSourceClient

        client = UnifiedSourceClient()
        status = client.status()

        assert "sources" in status
        assert "pubmed_available" in status


class TestSourcesPackageNew:
    """Tests for sources package exports."""

    def test_package_imports(self):
        """Test all exports are available."""
        from jarvis_core.sources import (
            OpenAlexClient,
            PubMedClient,
            SemanticScholarClient,
            UnifiedSourceClient,
        )

        assert PubMedClient is not None
        assert SemanticScholarClient is not None
        assert OpenAlexClient is not None
        assert UnifiedSourceClient is not None
