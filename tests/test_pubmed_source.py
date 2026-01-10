"""Tests for trend.sources.pubmed module."""

from jarvis_core.trend.sources.pubmed import PubMedSource


class TestPubMedSource:
    def test_name_property(self):
        source = PubMedSource()
        assert source.name == "pubmed"

    def test_is_available(self):
        source = PubMedSource()
        assert source.is_available() is True

    def test_fetch_basic(self):
        source = PubMedSource()
        items = source.fetch(["cancer treatment"], max_results=6)
        
        assert len(items) > 0
        assert all(item.source == "pubmed" for item in items)

    def test_fetch_multiple_queries(self):
        source = PubMedSource()
        items = source.fetch(["immunotherapy", "checkpoint inhibitor"], max_results=10)
        
        # Should get items for both queries
        assert len(items) > 0

    def test_search_pubmed_mock_results(self):
        source = PubMedSource()
        items = source._search_pubmed("test query", max_results=5)
        
        # Mock returns max 3 items
        assert len(items) <= 3
        assert all("pmid:" in item.id for item in items)
        assert all(item.url.startswith("https://pubmed.ncbi.nlm.nih.gov") for item in items)

    def test_fetch_oa_flag(self):
        source = PubMedSource()
        items = source.fetch(["test"], max_results=3)
        
        # Mock returns non-OA items
        assert all(item.is_oa is False for item in items)
