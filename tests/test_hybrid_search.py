"""Tests for the Hybrid Search Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 1.2
Updated to match actual implementation.
"""

import numpy as np
import pytest


class TestBM25Index:
    """Tests for BM25 index."""

    def test_bm25_initialization(self):
        """Test BM25Index initialization."""
        from jarvis_core.embeddings import BM25Index

        index = BM25Index()
        assert index is not None

    def test_bm25_build(self):
        """Test building BM25 index from corpus."""
        from jarvis_core.embeddings import BM25Index

        index = BM25Index()

        corpus = [
            "machine learning for medical diagnosis",
            "deep learning neural networks",
            "clinical trial randomized controlled",
        ]
        ids = ["1", "2", "3"]

        index.build(corpus, ids)

        assert index.doc_count == 3

    def test_bm25_search(self):
        """Test BM25 search."""
        from jarvis_core.embeddings import BM25Index

        index = BM25Index()

        corpus = [
            "machine learning for medical diagnosis",
            "deep learning neural networks image classification",
            "clinical trial randomized controlled study",
        ]
        ids = ["1", "2", "3"]

        index.build(corpus, ids)

        results = index.search("machine learning", top_k=2)

        assert len(results) <= 2
        # Results are tuples of (doc_id, score)
        assert results[0][0] == "1"  # Most relevant

    def test_bm25_add_document(self):
        """Test adding single document to BM25 index."""
        from jarvis_core.embeddings import BM25Index

        index = BM25Index()
        index.build(["initial document"], ["0"])

        index.add_document("1", "new document added")

        assert index.doc_count == 2
        assert index.get_document("1") == "new document added"

    def test_bm25_empty_query(self):
        """Test BM25 with empty query."""
        from jarvis_core.embeddings import BM25Index

        index = BM25Index()
        index.build(["test document"], ["1"])

        results = index.search("", top_k=5)

        assert len(results) == 0


class TestSentenceTransformerEmbedding:
    """Tests for Sentence Transformer embeddings."""

    def test_embedding_initialization(self):
        """Test SentenceTransformerEmbedding initialization."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding

        embedder = SentenceTransformerEmbedding()
        assert embedder is not None

    def test_encode_single_text(self):
        """Test encoding single text."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding

        embedder = SentenceTransformerEmbedding()

        # encode returns 2D array even for single text
        embedding = embedder.encode("This is a test sentence.")

        assert isinstance(embedding, np.ndarray)
        # Shape is (1, dim) for single text
        assert len(embedding.shape) in [1, 2]
        if embedding.ndim == 2:
            assert embedding.shape[0] == 1

    def test_encode_batch(self):
        """Test encoding batch of texts."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding

        embedder = SentenceTransformerEmbedding()

        texts = [
            "First document about machine learning",
            "Second document about clinical trials",
            "Third document about data analysis",
        ]

        # Use encode method with batch
        embeddings = embedder.encode(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 3

    def test_embedding_similarity(self):
        """Test embedding similarity."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding

        embedder = SentenceTransformerEmbedding()

        # encode returns 2D, get first row
        emb1 = embedder.encode("machine learning")[0]
        emb2 = embedder.encode("artificial intelligence")[0]
        emb3 = embedder.encode("cooking recipes")[0]

        # Cosine similarity
        def cosine_sim(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        sim_related = cosine_sim(emb1, emb2)
        sim_unrelated = cosine_sim(emb1, emb3)

        assert sim_related > sim_unrelated


class TestHybridSearch:
    """Tests for Hybrid Search."""

    def test_hybrid_search_initialization(self):
        """Test HybridSearch initialization."""
        from jarvis_core.embeddings import HybridSearch

        search = HybridSearch()
        assert search is not None

    def test_hybrid_search_index(self):
        """Test indexing documents in hybrid search."""
        from jarvis_core.embeddings import HybridSearch

        search = HybridSearch()

        corpus = [
            "machine learning medical diagnosis",
            "deep learning computer vision",
        ]
        ids = ["1", "2"]

        search.index(corpus, ids)

        # doc_count is a property
        assert search.doc_count == 2

    def test_hybrid_search_query(self):
        """Test hybrid search query."""
        from jarvis_core.embeddings import HybridSearch

        search = HybridSearch()

        corpus = [
            "machine learning for medical diagnosis treatment",
            "deep learning computer vision image processing",
            "clinical trial drug efficacy randomized study",
        ]
        ids = ["1", "2", "3"]

        search.index(corpus, ids)

        results = search.search("machine learning medical", top_k=2)

        assert len(results.results) <= 2
        # First result should be the most relevant
        if results.results:
            assert results.results[0].doc_id == "1"

    def test_hybrid_search_rrf_fusion(self):
        """Test RRF fusion method."""
        from jarvis_core.embeddings import FusionMethod, HybridSearch

        search = HybridSearch(fusion_method=FusionMethod.RRF)

        corpus = [
            "cancer treatment chemotherapy oncology",
            "cancer diagnosis with machine learning AI",
            "heart disease prevention cardiology",
        ]
        ids = ["1", "2", "3"]

        search.index(corpus, ids)

        results = search.search("cancer machine learning", top_k=3)

        # Should return results
        assert len(results.results) > 0

    def test_hybrid_search_weights(self):
        """Test hybrid search with custom weights."""
        from jarvis_core.embeddings import HybridSearch

        # Use actual parameter names from implementation
        search_sparse_heavy = HybridSearch(dense_weight=0.2, sparse_weight=0.8)
        search_dense_heavy = HybridSearch(dense_weight=0.8, sparse_weight=0.2)

        corpus = [
            "randomized controlled trial RCT study",
            "experimental study with random assignment design",
        ]
        ids = ["1", "2"]

        search_sparse_heavy.index(corpus, ids)
        search_dense_heavy.index(corpus, ids)

        # Query with exact keyword
        results_sparse = search_sparse_heavy.search("RCT", top_k=2)
        results_dense = search_dense_heavy.search("RCT", top_k=2)

        # Both should return results
        assert len(results_sparse.results) > 0
        assert len(results_dense.results) > 0


class TestFusionMethod:
    """Tests for fusion methods."""

    def test_fusion_method_enum(self):
        """Test FusionMethod enum."""
        from jarvis_core.embeddings import FusionMethod

        assert FusionMethod.RRF.value == "rrf"
        assert FusionMethod.LINEAR.value == "linear"




class TestSPECTER2:
    """Tests for SPECTER2 scientific embeddings."""

    def test_specter2_initialization(self):
        """Test SPECTER2Embedding initialization."""
        from jarvis_core.embeddings import SPECTER2Embedding

        embedder = SPECTER2Embedding()
        assert embedder is not None

    @pytest.mark.skip(reason="SPECTER2 requires peft package which is not installed")
    def test_specter2_encode(self):
        """Test SPECTER2 encoding."""
        from jarvis_core.embeddings import SPECTER2Embedding

        embedder = SPECTER2Embedding()

        # SPECTER2.embed takes list of texts
        text = "[Title] A randomized controlled trial of aspirin [Abstract] We conducted a double-blind RCT..."
        embeddings = embedder.embed([text])

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 1  # 1 text
        assert embeddings.ndim == 2


class TestGetEmbeddingModel:
    """Tests for get_embedding_model factory."""

    def test_get_general_model(self):
        """Test getting general embedding model."""
        from jarvis_core.embeddings import get_embedding_model

        model = get_embedding_model("general")

        assert model is not None

    def test_get_scientific_model(self):
        """Test getting scientific embedding model."""
        from jarvis_core.embeddings import get_embedding_model

        model = get_embedding_model("scientific")

        assert model is not None


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.embeddings import (
            BM25Index,
            FusionMethod,
            HybridSearch,
            SentenceTransformerEmbedding,
        )

        assert SentenceTransformerEmbedding is not None
        assert BM25Index is not None
        assert HybridSearch is not None
        assert FusionMethod is not None
