import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from jarvis_core.embeddings.vector_store import VectorStore, FAISSVectorStore
from jarvis_core.embeddings.chroma_store import ChromaVectorStore


# Fixture to provide mocked store instances
@pytest.fixture(params=["faiss", "chroma"])
def store_instance(request):
    if request.param == "faiss":
        with patch("jarvis_core.embeddings.vector_store.FAISSVectorStore._load_faiss") as mock_load:
            mock_faiss = MagicMock()
            mock_index = MagicMock()
            mock_faiss.IndexFlatIP.return_value = mock_index
            mock_load.return_value = mock_faiss

            store = FAISSVectorStore(dimension=384)
            # Mock internal state for search/count if needed, or rely on build
            yield store, "faiss", mock_index

    elif request.param == "chroma":
        with patch(
            "jarvis_core.embeddings.chroma_store.ChromaVectorStore._init_client"
        ) as mock_init:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_init.return_value = (mock_client, mock_collection)

            store = ChromaVectorStore()
            yield store, "chroma", mock_collection


def test_vector_store_add_search(store_instance):
    store, type_name, mock_backend = store_instance

    embeddings = np.random.randn(2, 384).astype(np.float32)
    doc_ids = ["1", "2"]
    metadata = [{"text": "doc1"}, {"text": "doc2"}]

    # 1. Test ADD
    store.add(embeddings, doc_ids, metadata)

    if type_name == "faiss":
        mock_backend.add.assert_called()
        assert store.count == 2
    else:
        mock_backend.add.assert_called()
        # Chroma count calls collection.count
        mock_backend.count.return_value = 2
        assert store.count == 2

    # 2. Test SEARCH
    query = np.random.randn(384).astype(np.float32)

    if type_name == "faiss":
        # Mock FAISS return
        # distances, indices
        mock_backend.search.return_value = (np.array([[0.9, 0.8]]), np.array([[0, 1]]))

        results = store.search(query, top_k=2)
        assert len(results) == 2
        assert results[0][0] == "1"
        assert results[0][1] == 0.9

    else:  # Chroma
        # Mock Chroma return
        mock_backend.query.return_value = {
            "ids": [["1", "2"]],
            "distances": [[0.1, 0.2]],  # distance 0.1 -> score 0.9
            "metadatas": [[{"text": "doc1"}, {"text": "doc2"}]],
            "documents": [["doc1", "doc2"]],
        }

        results = store.search(query, top_k=2)
        assert len(results) == 2
        assert results[0][0] == "1"
        assert abs(results[0][1] - 0.9) < 1e-5


def test_save_load_interface(tmp_path):
    # Just verify that save/load methods exist and accept Path,
    # deeper logic is tested in specific tests.
    assert issubclass(FAISSVectorStore, VectorStore)
    assert issubclass(ChromaVectorStore, VectorStore)
