"""Tests for FAISS Vector Store."""

from unittest.mock import MagicMock, patch

import numpy as np


def test_faiss_vector_store_build():
    with patch("jarvis_core.embeddings.vector_store.FAISSVectorStore._load_faiss") as mock_load:
        mock_faiss = MagicMock()
        mock_index = MagicMock()
        mock_faiss.IndexFlatIP.return_value = mock_index
        mock_load.return_value = mock_faiss

        from jarvis_core.embeddings.vector_store import FAISSVectorStore

        store = FAISSVectorStore(dimension=384)
        embeddings = np.random.randn(10, 384).astype(np.float32)
        doc_ids = [f"doc_{i}" for i in range(10)]

        store.build(embeddings, doc_ids)

        assert store.count == 10
        mock_faiss.IndexFlatIP.assert_called_once_with(384)
        mock_index.add.assert_called_once()


def test_faiss_vector_store_search():
    with patch("jarvis_core.embeddings.vector_store.FAISSVectorStore._load_faiss") as mock_load:
        mock_faiss = MagicMock()
        mock_index = MagicMock()
        mock_faiss.IndexFlatIP.return_value = mock_index
        mock_load.return_value = mock_faiss

        # Mock search results
        mock_index.search.return_value = (np.array([[0.9, 0.8, 0.7]]), np.array([[0, 1, 2]]))

        from jarvis_core.embeddings.vector_store import FAISSVectorStore

        store = FAISSVectorStore(dimension=384)
        store._index = mock_index
        store._doc_ids = ["doc_0", "doc_1", "doc_2"]
        store._metadata = [{}, {}, {}]

        query = np.random.randn(384).astype(np.float32)
        results = store.search(query, top_k=3)

        assert len(results) == 3
        assert results[0][0] == "doc_0"
        assert results[0][1] == 0.9


def test_faiss_normalize():
    from jarvis_core.embeddings.vector_store import FAISSVectorStore

    store = FAISSVectorStore(dimension=3)

    vec = np.array([[3.0, 4.0, 0.0]])
    normalized = store._normalize(vec)

    # L2 norm should be 1
    assert np.allclose(np.linalg.norm(normalized), 1.0)
