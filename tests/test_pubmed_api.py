"""Tests for PubMed API client."""

from jarvis_core.integrations.pubmed import (
    MockPubMedClient,
    PaperResult,
    PubMedClient,
    get_pubmed_client,
    search_papers,
)
import pytest


class TestPaperResult:
    """Test PaperResult dataclass."""

    def test_create_paper_result(self):
        """Test creating a paper result."""
        paper = PaperResult(
            pmid="12345678",
            title="Test Paper",
            authors=["Smith J", "Johnson A"],
            journal="Nature",
            pub_date="2024 Jan",
            abstract="This is a test abstract.",
        )
        assert paper.pmid == "12345678"
        assert paper.title == "Test Paper"
        assert len(paper.authors) == 2

    def test_paper_result_to_dict(self):
        """Test converting paper result to dict."""
        paper = PaperResult(
            pmid="12345678",
            title="Test Paper",
            authors=["Smith J"],
            journal="Nature",
            pub_date="2024 Jan",
            abstract="This is a test abstract.",
        )
        data = paper.to_dict()

        assert "pmid" in data
        assert "url" in data
        assert "pubmed.ncbi.nlm.nih.gov" in data["url"]

    def test_paper_result_truncates_long_abstract(self):
        """Test that long abstracts are truncated."""
        long_abstract = "A" * 300
        paper = PaperResult(
            pmid="12345678",
            title="Test",
            authors=[],
            journal="Test",
            pub_date="2024",
            abstract=long_abstract,
        )
        data = paper.to_dict()
        assert len(data["abstract"]) < 250
        assert data["abstract"].endswith("...")

class TestMockPubMedClient:
    """Test mock PubMed client."""

    def test_mock_client_returns_results(self):
        """Test mock client returns results."""
        client = MockPubMedClient()
        results = client.search_and_fetch("COVID-19", max_results=5)

        assert len(results) > 0
        assert len(results) <= 5

    def test_mock_client_result_structure(self):
        """Test mock client returns proper structure."""
        client = MockPubMedClient()
        results = client.search_and_fetch("cancer", max_results=1)

        if results:
            paper = results[0]
            assert "pmid" in paper
            assert "title" in paper
            assert "authors" in paper
            assert "journal" in paper
            assert "url" in paper

    def test_mock_client_includes_query_in_title(self):
        """Test mock results include query term."""
        client = MockPubMedClient()
        query = "diabetes"
        results = client.search_and_fetch(query, max_results=3)

        # At least one result should mention query
        titles = [r["title"] for r in results]
        assert any(query in t.lower() for t in titles)

class TestPubMedClient:
    """Test real PubMed client (structure only, no network)."""

    def test_client_init(self):
        """Test client initialization."""
        client = PubMedClient()
        assert client.api_key is None

        client_with_key = PubMedClient(api_key="test_key")
        assert client_with_key.api_key == "test_key"

    def test_base_url(self):
        """Test base URL is correct."""
        client = PubMedClient()
        assert "eutils.ncbi.nlm.nih.gov" in client.BASE_URL

class TestSearchPapers:
    """Test search_papers convenience function."""

    def test_search_papers_with_mock(self):
        """Test search_papers with mock client."""
        results = search_papers("test query", max_results=3, use_mock=True)

        assert isinstance(results, list)
        assert len(results) <= 3

    def test_search_papers_returns_dicts(self):
        """Test search_papers returns dictionaries."""
        results = search_papers("AI", max_results=1, use_mock=True)

        if results:
            assert isinstance(results[0], dict)

class TestGetPubMedClient:
    """Test client factory function."""

    def test_get_mock_client(self):
        """Test getting mock client."""
        client = get_pubmed_client(use_mock=True)
        assert isinstance(client, MockPubMedClient)

    def test_get_real_client(self):
        """Test getting real client."""
        client = get_pubmed_client(use_mock=False)
        assert isinstance(client, PubMedClient)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
