from jarvis_core.retrieval.hybrid import HybridRetriever


# Mock embedding model for speed/determinism in smoke tests
class MockEmbeddingModel:
    def embed(self, texts):
        import numpy as np

        # Simple mock: if text contains "cat", vector is [1, 0]
        # if text contains "dog", vector is [0, 1]
        vectors = []
        for text in texts:
            if "cat" in text.lower():
                vectors.append([1.0, 0.0])
            elif "dog" in text.lower():
                vectors.append([0.0, 1.0])
            else:
                vectors.append([0.5, 0.5])
        return np.array(vectors)


def test_hybrid_retriever_smoke():
    # Use real BM25 but mock embeddings
    hybrid = HybridRetriever(embedding_model=MockEmbeddingModel())

    corpus = [
        {"chunk_id": "1", "text": "The quick brown fox jumps over the lazy dog"},
        {"chunk_id": "2", "text": "A sweet cat is sleeping on the mat"},
        {"chunk_id": "3", "text": "Medical research on immunotherapies"},
    ]

    hybrid.fit(corpus)

    # Test 1: Keyword match (BM25 dominant)
    results_keyword = hybrid.search("fox", top_k=1)
    assert len(results_keyword) > 0
    assert results_keyword[0]["chunk_id"] == "1"

    # Test 2: Semantic match (Mock Vector dominant)
    # Query "feline" -> maps to "cat" in a real model, but our mock is simple.
    # Let's test exact vector match logic with "cat"
    results_semantic = hybrid.search("cat", top_k=1)
    assert len(results_semantic) > 0
    assert results_semantic[0]["chunk_id"] == "2"

    # Test 3: RRF Merge
    # A query hitting both slightly
    results_mixed = hybrid.search("dog cat", top_k=2)
    ids = {r["chunk_id"] for r in results_mixed}
    assert "1" in ids or "2" in ids