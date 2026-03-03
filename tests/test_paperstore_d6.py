"""Tests for ChromaDB PaperStore (D6)."""
import pytest
from jarvis_core.embeddings.paper_store import PaperStore


class TestPaperStoreD6:
    def test_init(self):
        store = PaperStore()
        assert store is not None

    def test_count(self):
        store = PaperStore()
        c = store.count()
        assert isinstance(c, int)
        assert c >= 0

    def test_search_returns_list(self):
        store = PaperStore()
        if store.count() == 0:
            pytest.skip("ChromaDB is empty, skipping search test")
        results = store.search("PD-1 immunotherapy", top_k=3)
        assert isinstance(results, list)
        assert len(results) <= 3

    def test_add_and_search(self, sample_papers, tmp_path):
        store = PaperStore(persist_dir=str(tmp_path / ".chroma_test"))
        count = store.add_papers(sample_papers)
        assert count == 3
        results = store.search("autophagy aging", top_k=2)
        assert isinstance(results, list)
        assert len(results) > 0
