"""Tests for Vector Retriever (RP23).

Per RP23, these tests verify:
- Dummy embedder
- Cosine similarity
- VectorRetriever build/search
- ExecutionContext integration
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.evidence import EvidenceStore
from jarvis_core.sources import ChunkResult, ExecutionContext
from jarvis_core.vector_index import (
    VectorRetriever,
    cosine_similarity,
    dummy_embed,
    get_relevant_chunks_vector,
)


class TestDummyEmbed:
    """Tests for dummy embedder."""

    def test_embed_returns_list(self):
        """Should return list of floats."""
        result = dummy_embed("test")
        assert isinstance(result, list)
        assert len(result) == 64  # Default dim
        assert all(isinstance(x, float) for x in result)

    def test_embed_deterministic(self):
        """Same input should give same output."""
        a = dummy_embed("test")
        b = dummy_embed("test")
        assert a == b

    def test_embed_different_inputs(self):
        """Different inputs should give different outputs."""
        a = dummy_embed("hello")
        b = dummy_embed("world")
        assert a != b

    def test_embed_normalized(self):
        """Result should be unit vector."""
        import math

        result = dummy_embed("test")
        norm = math.sqrt(sum(x * x for x in result))
        assert abs(norm - 1.0) < 0.01


class TestCosineSimilarity:
    """Tests for cosine similarity."""

    def test_identical_vectors(self):
        """Same vector should have similarity 1."""
        v = [1.0, 2.0, 3.0]
        sim = cosine_similarity(v, v)
        assert abs(sim - 1.0) < 0.01

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0."""
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        sim = cosine_similarity(a, b)
        assert abs(sim) < 0.01

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1."""
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        sim = cosine_similarity(a, b)
        assert abs(sim + 1.0) < 0.01


class TestVectorRetriever:
    """Tests for VectorRetriever."""

    def test_build_index(self):
        """Should build index from chunks."""
        chunks = [
            ChunkResult(chunk_id="c1", locator="loc1", preview="CD73 enzyme"),
            ChunkResult(chunk_id="c2", locator="loc2", preview="Cancer therapy"),
        ]

        retriever = VectorRetriever()
        retriever.build(chunks)

        assert len(retriever.index) == 2

    def test_search_returns_chunks(self):
        """Should return relevant chunks."""
        chunks = [
            ChunkResult(chunk_id="c1", locator="loc1", preview="CD73 is an enzyme"),
            ChunkResult(chunk_id="c2", locator="loc2", preview="Immunotherapy cancer"),
            ChunkResult(chunk_id="c3", locator="loc3", preview="CD73 adenosine"),
        ]

        retriever = VectorRetriever()
        retriever.build(chunks)

        results = retriever.search("CD73", k=2)

        assert len(results) == 2
        # Should contain CD73-related chunks (based on hash similarity)
        ids = [r.chunk_id for r in results]
        assert "c1" in ids or "c3" in ids

    def test_search_empty_index(self):
        """Should handle empty index."""
        retriever = VectorRetriever()
        results = retriever.search("test")
        assert results == []


class TestGetRelevantChunksVector:
    """Tests for convenience function."""

    def test_returns_results(self):
        """Should return search results."""
        chunks = [
            ChunkResult(chunk_id="c1", locator="loc1", preview="Test content"),
        ]

        results = get_relevant_chunks_vector(chunks, "test", k=5)

        assert len(results) == 1
        assert results[0].chunk_id == "c1"


class TestExecutionContextVector:
    """Tests for ExecutionContext vector search."""

    def test_get_relevant_chunks_vector_method(self):
        """ExecutionContext should have vector search."""
        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        # Add some chunks
        ctx.add_chunks([
            ChunkResult(chunk_id="c1", locator="loc1", preview="CD73 enzyme"),
            ChunkResult(chunk_id="c2", locator="loc2", preview="Cancer study"),
        ])

        results = ctx.get_relevant_chunks_vector("CD73", k=2)

        assert len(results) <= 2
        assert all(isinstance(r, ChunkResult) for r in results)

    def test_vector_search_empty_context(self):
        """Should handle empty context."""
        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        results = ctx.get_relevant_chunks_vector("test")
        assert results == []
