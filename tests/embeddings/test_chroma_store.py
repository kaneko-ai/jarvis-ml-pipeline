"""Tests for ChromaDB Vector Store."""

from unittest.mock import MagicMock, patch


def test_chroma_vector_store_add():
    with patch("jarvis_core.embeddings.chroma_store.ChromaVectorStore._init_client") as mock_init:
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_init.return_value = (mock_client, mock_collection)

        from jarvis_core.embeddings.chroma_store import ChromaVectorStore

        store = ChromaVectorStore()
        store.add(
            texts=["doc1", "doc2"],
            embeddings=[[0.1] * 384, [0.2] * 384],
            ids=["id1", "id2"],
            metadata=[{"title": "Title1"}, {"title": "Title2"}],
        )

        mock_collection.add.assert_called_once()


def test_chroma_vector_store_search():
    with patch("jarvis_core.embeddings.chroma_store.ChromaVectorStore._init_client") as mock_init:
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_init.return_value = (mock_client, mock_collection)

        # Mock query results
        mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"title": "T1"}, {"title": "T2"}]],
            "distances": [[0.1, 0.2]],
        }

        from jarvis_core.embeddings.chroma_store import ChromaVectorStore

        store = ChromaVectorStore()
        results = store.search(query_embedding=[0.1] * 384, top_k=2)

        assert len(results) == 2
        assert results[0][0] == "id1"
        assert results[0][2] == "doc1"


def test_chroma_vector_store_count():
    with patch("jarvis_core.embeddings.chroma_store.ChromaVectorStore._init_client") as mock_init:
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 100
        mock_init.return_value = (mock_client, mock_collection)

        from jarvis_core.embeddings.chroma_store import ChromaVectorStore

        store = ChromaVectorStore()
        assert store.count == 100
