"""Tests for vector_index module."""

from unittest.mock import MagicMock

from jarvis_core.vector_index import (
    dummy_embed,
    cosine_similarity,
    IndexedChunk,
    VectorRetriever,
    get_relevant_chunks_vector,
)


class TestDummyEmbed:
    def test_returns_correct_dimension(self):
        result = dummy_embed("test text", dim=64)
        
        assert len(result) == 64

    def test_deterministic(self):
        result1 = dummy_embed("test text")
        result2 = dummy_embed("test text")
        
        assert result1 == result2

    def test_different_texts_different_embeddings(self):
        result1 = dummy_embed("text one")
        result2 = dummy_embed("text two")
        
        assert result1 != result2

    def test_normalized(self):
        import math
        result = dummy_embed("test text")
        norm = math.sqrt(sum(v * v for v in result))
        
        assert abs(norm - 1.0) < 0.01


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 0.5, 0.5]
        result = cosine_similarity(v, v)
        
        assert abs(result - 1.0) < 0.01

    def test_orthogonal_vectors(self):
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        result = cosine_similarity(v1, v2)
        
        assert abs(result) < 0.01

    def test_different_lengths(self):
        v1 = [1.0, 0.5]
        v2 = [1.0, 0.5, 0.5]
        result = cosine_similarity(v1, v2)
        
        assert result == 0.0

    def test_zero_vector(self):
        v1 = [1.0, 0.5]
        v2 = [0.0, 0.0]
        result = cosine_similarity(v1, v2)
        
        assert result == 0.0


class TestIndexedChunk:
    def test_creation(self):
        chunk = IndexedChunk(
            chunk_id="c1",
            locator="loc:1",
            text="test text",
            preview="test...",
            vector=[0.1, 0.2, 0.3],
        )
        
        assert chunk.chunk_id == "c1"
        assert len(chunk.vector) == 3


class TestVectorRetriever:
    def make_mock_chunk(self, chunk_id: str, preview: str):
        mock = MagicMock()
        mock.chunk_id = chunk_id
        mock.locator = f"loc:{chunk_id}"
        mock.preview = preview
        return mock

    def test_init(self):
        retriever = VectorRetriever()
        
        assert retriever.dim == 64
        assert retriever.index == []

    def test_build_creates_index(self):
        retriever = VectorRetriever()
        chunks = [
            self.make_mock_chunk("c1", "cancer research"),
            self.make_mock_chunk("c2", "diabetes study"),
        ]
        
        retriever.build(chunks)
        
        assert len(retriever.index) == 2

    def test_search_returns_results(self):
        retriever = VectorRetriever()
        chunks = [
            self.make_mock_chunk("c1", "cancer immunotherapy research"),
            self.make_mock_chunk("c2", "diabetes medication study"),
        ]
        
        retriever.build(chunks)
        results = retriever.search("cancer", k=2)
        
        assert len(results) <= 2
        assert all(hasattr(r, "chunk_id") for r in results)

    def test_search_empty_index(self):
        retriever = VectorRetriever()
        results = retriever.search("query")
        
        assert results == []


class TestGetRelevantChunksVector:
    def make_mock_chunk(self, chunk_id: str, preview: str):
        mock = MagicMock()
        mock.chunk_id = chunk_id
        mock.locator = f"loc:{chunk_id}"
        mock.preview = preview
        return mock

    def test_convenience_function(self):
        chunks = [
            self.make_mock_chunk("c1", "relevant text"),
            self.make_mock_chunk("c2", "other content"),
        ]
        
        results = get_relevant_chunks_vector(chunks, "relevant", k=1)
        
        assert len(results) <= 1
