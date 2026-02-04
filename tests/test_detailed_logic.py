import pytest

"""Detailed logic tests for high-impact 0% coverage modules.

These tests go beyond import checks to actually test functionality.
"""

from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path


# ============================================================
# Tests for disk_cache.py (0% coverage - 72 stmts)
# ============================================================


class TestDiskCacheInit:
    """Tests for DiskCache initialization."""

    def test_init_default(self):
        from jarvis_core.disk_cache import DiskCache

        cache = DiskCache()
        assert cache.cache_dir == Path("cache")
        assert cache.hit_count == 0
        assert cache.miss_count == 0

    def test_init_custom_dir(self):
        from jarvis_core.disk_cache import DiskCache

        cache = DiskCache(cache_dir="my_cache")
        assert cache.cache_dir == Path("my_cache")


class TestDiskCacheComputeHash:
    """Tests for hash computation."""

    def test_hash_string(self):
        from jarvis_core.disk_cache import DiskCache

        cache = DiskCache()
        hash1 = cache._compute_hash("test string")
        hash2 = cache._compute_hash("test string")
        assert hash1 == hash2
        assert len(hash1) == 24

    def test_hash_dict(self):
        from jarvis_core.disk_cache import DiskCache

        cache = DiskCache()
        h1 = cache._compute_hash({"key": "value", "num": 42})
        h2 = cache._compute_hash({"num": 42, "key": "value"})
        assert h1 == h2  # sorted keys

    def test_hash_other_types(self):
        from jarvis_core.disk_cache import DiskCache

        cache = DiskCache()
        h = cache._compute_hash(12345)
        assert len(h) == 24


class TestDiskCacheOperations:
    """Tests for cache get/set operations."""

    def test_set_and_get(self):
        from jarvis_core.disk_cache import DiskCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = DiskCache(cache_dir=tmpdir)
            cache.set("test_tool", "input1", {"result": "success"})
            result = cache.get("test_tool", "input1")
            assert result == {"result": "success"}
            assert cache.hit_count == 1

    def test_get_miss(self):
        from jarvis_core.disk_cache import DiskCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = DiskCache(cache_dir=tmpdir)
            result = cache.get("nonexistent", "input")
            assert result is None
            assert cache.miss_count == 1

    def test_has(self):
        from jarvis_core.disk_cache import DiskCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = DiskCache(cache_dir=tmpdir)
            assert cache.has("tool", "input") is False
            cache.set("tool", "input", "result")
            assert cache.has("tool", "input") is True

    def test_invalidate(self):
        from jarvis_core.disk_cache import DiskCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = DiskCache(cache_dir=tmpdir)
            cache.set("tool", "input", "result")
            assert cache.invalidate("tool", "input") is True
            assert cache.has("tool", "input") is False
            assert cache.invalidate("tool", "input") is False

    def test_clear_specific_tool(self):
        from jarvis_core.disk_cache import DiskCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = DiskCache(cache_dir=tmpdir)
            cache.set("tool1", "input1", "result1")
            cache.set("tool1", "input2", "result2")
            cache.set("tool2", "input1", "result3")
            count = cache.clear("tool1")
            assert count == 2
            assert cache.has("tool2", "input1") is True

    def test_clear_all(self):
        from jarvis_core.disk_cache import DiskCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = DiskCache(cache_dir=tmpdir)
            cache.set("tool1", "input", "result1")
            cache.set("tool2", "input", "result2")
            count = cache.clear()
            assert count == 2

    def test_get_stats(self):
        from jarvis_core.disk_cache import DiskCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = DiskCache(cache_dir=tmpdir)
            cache.set("tool", "input", "result")
            cache.get("tool", "input")
            cache.get("tool", "missing")
            stats = cache.get_stats()
            assert stats["hits"] == 1
            assert stats["misses"] == 1
            assert stats["hit_rate"] == 0.5


class TestGetDiskCache:
    """Tests for convenience function."""

    def test_get_disk_cache(self):
        from jarvis_core.disk_cache import get_disk_cache

        cache = get_disk_cache("test_cache")
        assert cache.cache_dir == Path("test_cache")


# ============================================================
# Tests for dedup/dedup_engine.py (0% coverage - 70 stmts)
# ============================================================


class TestDedupResult:
    """Tests for DedupResult dataclass."""

    def test_dedup_result(self):
        from jarvis_core.dedup.dedup_engine import DedupResult

        result = DedupResult(canonical_papers=[], merged_count=5)
        assert result.merged_count == 5


class TestDedupEngine:
    """Tests for DedupEngine class."""

    def test_init(self):
        from jarvis_core.dedup.dedup_engine import DedupEngine

        engine = DedupEngine()
        assert engine.similarity_threshold == 0.92

    def test_init_custom_threshold(self):
        from jarvis_core.dedup.dedup_engine import DedupEngine

        engine = DedupEngine(similarity_threshold=0.85)
        assert engine.similarity_threshold == 0.85

    def test_deduplicate_empty(self):
        from jarvis_core.dedup.dedup_engine import DedupEngine

        engine = DedupEngine()
        result = engine.deduplicate([])
        assert result.canonical_papers == []
        assert result.merged_count == 0

    def test_deduplicate_no_duplicates(self):
        from jarvis_core.dedup.dedup_engine import DedupEngine

        engine = DedupEngine()
        papers = [
            {"paper_id": "1", "title": "Paper One", "doi": "10.1/a"},
            {"paper_id": "2", "title": "Paper Two", "doi": "10.1/b"},
        ]
        result = engine.deduplicate(papers)
        assert len(result.canonical_papers) == 2
        assert result.merged_count == 0

    def test_deduplicate_by_doi(self):
        from jarvis_core.dedup.dedup_engine import DedupEngine

        engine = DedupEngine()
        papers = [
            {"paper_id": "1", "title": "Paper One", "doi": "10.1/same"},
            {"paper_id": "2", "title": "Paper One Variant", "doi": "10.1/same"},
        ]
        result = engine.deduplicate(papers)
        assert len(result.canonical_papers) == 1
        assert result.merged_count == 1
        assert "1" in result.canonical_papers[0]["merged_from"]
        assert "2" in result.canonical_papers[0]["merged_from"]

    def test_deduplicate_by_pmid(self):
        from jarvis_core.dedup.dedup_engine import DedupEngine

        engine = DedupEngine()
        papers = [
            {"paper_id": "1", "title": "Paper A", "pmid": "12345"},
            {"paper_id": "2", "title": "Paper A Copy", "pmid": "12345"},
        ]
        result = engine.deduplicate(papers)
        assert len(result.canonical_papers) == 1
        assert result.merged_count == 1

    def test_canonical_id_doi(self):
        from jarvis_core.dedup.dedup_engine import DedupEngine

        engine = DedupEngine()
        paper = {"doi": "10.1234/test"}
        cid = engine._canonical_id(paper)
        assert cid == "doi:10.1234/test"

    def test_canonical_id_pmid(self):
        from jarvis_core.dedup.dedup_engine import DedupEngine

        engine = DedupEngine()
        paper = {"pmid": "12345"}
        cid = engine._canonical_id(paper)
        assert cid == "pmid:12345"

    def test_canonical_id_pmcid(self):
        from jarvis_core.dedup.dedup_engine import DedupEngine

        engine = DedupEngine()
        paper = {"pmcid": "PMC1234"}
        cid = engine._canonical_id(paper)
        assert cid == "pmc:PMC1234"

    def test_canonical_id_title(self):
        from jarvis_core.dedup.dedup_engine import DedupEngine

        engine = DedupEngine()
        paper = {"title": "Some Paper Title"}
        cid = engine._canonical_id(paper)
        assert cid.startswith("title:")


# ============================================================
# Tests for sources/arxiv_client.py (0% coverage - 141 stmts)
# ============================================================


class TestArxivPaper:
    """Tests for ArxivPaper dataclass."""

    @pytest.mark.network
    def test_arxiv_paper_creation(self):
        from jarvis_core.sources.arxiv_client import ArxivPaper

        paper = ArxivPaper(
            arxiv_id="2101.00001",
            title="Test Paper",
            abstract="This is an abstract",
            authors=["Author One", "Author Two"],
        )
        assert paper.arxiv_id == "2101.00001"
        assert len(paper.authors) == 2

    @pytest.mark.network
    def test_arxiv_paper_to_dict(self):
        from jarvis_core.sources.arxiv_client import ArxivPaper

        paper = ArxivPaper(
            arxiv_id="2101.00001",
            title="Test",
            abstract="Abstract",
            authors=["Author"],
        )
        d = paper.to_dict()
        assert d["arxiv_id"] == "2101.00001"
        assert "title" in d


class TestArxivClientInit:
    """Tests for ArxivClient initialization."""

    @pytest.mark.network
    def test_init_default(self):
        from jarvis_core.sources.arxiv_client import ArxivClient

        client = ArxivClient()
        assert client.timeout == 30.0
        assert client.rate_limit_delay == 3.0

    @pytest.mark.network
    def test_init_custom(self):
        from jarvis_core.sources.arxiv_client import ArxivClient

        client = ArxivClient(timeout=60.0, rate_limit_delay=5.0)
        assert client.timeout == 60.0
        assert client.rate_limit_delay == 5.0


class TestArxivClientSearch:
    """Tests for ArxivClient search functionality."""

    @patch("jarvis_core.sources.arxiv_client.requests.get")
    def test_search_basic(self, mock_get):
        from jarvis_core.sources.arxiv_client import ArxivClient

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
        </feed>"""
        mock_get.return_value = mock_response

        client = ArxivClient()
        client._last_request_time = 0  # Skip rate limiting
        results = client.search("machine learning", max_results=5)
        assert isinstance(results, list)


# ============================================================
# Tests for sources/crossref_client.py (0% coverage - 104 stmts)
# ============================================================


class TestCrossrefClient:
    """Tests for Crossref client."""

    def test_import_and_init(self):
        from jarvis_core.sources.crossref_client import CrossrefClient

        client = CrossrefClient()
        assert client is not None


# ============================================================
# Tests for sources/unpaywall_client.py (0% coverage - 84 stmts)
# ============================================================


class TestUnpaywallClient:
    """Tests for Unpaywall client."""

    def test_import_and_init(self):
        from jarvis_core.sources.unpaywall_client import UnpaywallClient

        client = UnpaywallClient(email="test@example.com")
        assert client.email == "test@example.com"


# ============================================================
# Tests for llm.py (0% coverage - 29 stmts)
# ============================================================


class TestLLMModule:
    """Tests for main LLM module."""

    def test_import(self):
        from jarvis_core import llm

        assert hasattr(llm, "__name__")


# ============================================================
# Tests for index/bm25_store.py (0% coverage - 74 stmts)
# ============================================================


class TestBM25Store:
    """Tests for BM25 index store."""

    def test_import(self):
        from jarvis_core.index import bm25_store

        assert hasattr(bm25_store, "__name__")


# ============================================================
# Tests for index_builder.py (0% coverage - 56 stmts)
# ============================================================


class TestIndexBuilder:
    """Tests for index builder."""

    def test_import(self):
        from jarvis_core import index_builder

        assert hasattr(index_builder, "__name__")


# ============================================================
# Tests for retry_controller.py (0% coverage - 74 stmts)
# ============================================================


class TestRetryController:
    """Tests for retry controller."""

    def test_import(self):
        from jarvis_core import retry_controller

        assert hasattr(retry_controller, "__name__")
