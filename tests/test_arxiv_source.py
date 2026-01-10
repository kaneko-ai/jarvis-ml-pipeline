"""Tests for trend.sources.arxiv module."""

from jarvis_core.trend.sources.arxiv import ArxivSource


class TestArxivSource:
    def test_name_property(self):
        source = ArxivSource()
        assert source.name == "arxiv"

    def test_is_available(self):
        source = ArxivSource()
        assert source.is_available() is True

    def test_fetch_basic(self):
        source = ArxivSource()
        items = source.fetch(["machine learning"], max_results=6)
        
        assert len(items) > 0
        assert all(item.source == "arxiv" for item in items)
        assert all(item.is_oa is True for item in items)

    def test_fetch_multiple_queries(self):
        source = ArxivSource()
        items = source.fetch(["LLM", "RAG"], max_results=10)
        
        # Should get items for both queries
        assert len(items) > 0

    def test_search_arxiv_mock_results(self):
        source = ArxivSource()
        items = source._search_arxiv("test query", max_results=5)
        
        # Mock returns max 3 items
        assert len(items) <= 3
        assert all("arxiv:" in item.id for item in items)
        assert all(item.url.startswith("https://arxiv.org") for item in items)
