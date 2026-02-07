"""TD-028: Source client resilience tests.

API障害時の graceful degradation を検証するテスト。
既存テストは変更しない。
"""

from unittest.mock import MagicMock, patch

import pytest

from jarvis_core.sources.unified_source_client import SourceType, UnifiedPaper, UnifiedSourceClient


@pytest.fixture
def client() -> UnifiedSourceClient:
    return UnifiedSourceClient(email="test@example.com")


class TestSearchResilience:
    def test_all_sources_fail_returns_empty_list(self, client: UnifiedSourceClient) -> None:
        with (
            patch.object(client.pubmed, "search_and_fetch", side_effect=Exception("down")),
            patch.object(client.s2, "search", side_effect=Exception("down")),
            patch.object(client.openalex, "search", side_effect=Exception("down")),
        ):
            result = client.search("test query")
            assert isinstance(result, list)
            assert len(result) == 0

    def test_partial_failure_returns_partial_results(self, client: UnifiedSourceClient) -> None:
        mock_work = MagicMock()
        mock_work.openalex_id = "W123"
        mock_work.title = "Test Paper"
        mock_work.abstract = "Abstract"
        mock_work.authors = ["Author"]
        mock_work.publication_year = 2024
        mock_work.venue = "Journal"
        mock_work.doi = "10.1/test"
        mock_work.pmid = None
        mock_work.cited_by_count = 5
        mock_work.open_access_url = None
        mock_work.concepts = []
        mock_work.to_dict = lambda: {}

        with (
            patch.object(client.pubmed, "search_and_fetch", side_effect=Exception("fail")),
            patch.object(client.s2, "search", side_effect=Exception("fail")),
            patch.object(client.openalex, "search", return_value=[mock_work]),
        ):
            result = client.search("test")
            assert len(result) >= 1


class TestDOILookup:
    def test_all_fail_returns_none(self, client: UnifiedSourceClient) -> None:
        with (
            patch.object(client.openalex, "get_work", side_effect=Exception("fail")),
            patch.object(client.s2, "get_paper", side_effect=Exception("fail")),
        ):
            result = client.get_by_doi("10.1/nonexistent")
            assert result is None


class TestDeduplication:
    def test_dedup_by_doi(self, client: UnifiedSourceClient) -> None:
        papers = [
            UnifiedPaper(id="1", source=SourceType.PUBMED, title="A", doi="10.1/a"),
            UnifiedPaper(id="2", source=SourceType.OPENALEX, title="A copy", doi="10.1/a"),
            UnifiedPaper(id="3", source=SourceType.PUBMED, title="B", doi="10.1/b"),
        ]
        result = client._deduplicate(papers)
        assert len(result) == 2

    def test_no_doi_preserved(self, client: UnifiedSourceClient) -> None:
        papers = [
            UnifiedPaper(id="1", source=SourceType.PUBMED, title="A", doi=None),
            UnifiedPaper(id="2", source=SourceType.PUBMED, title="B", doi=None),
        ]
        result = client._deduplicate(papers)
        assert len(result) == 2
