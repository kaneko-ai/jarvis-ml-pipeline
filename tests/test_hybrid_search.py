"""Tests for the Hybrid Search Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 1.2
"""

import numpy as np


class TestBM25Index:
    """Tests for BM25 index."""

    def test_bm25_initialization(self):
        """Test BM25Index initialization."""
        from jarvis_core.embeddings import BM25Index

        index = BM25Index()
        assert index is not None

    def test_bm25_add_documents(self):
        """Test adding documents to BM25 index."""
        from jarvis_core.embeddings import BM25Index

        index = BM25Index()

        documents = [
            {"id": "1", "text": "machine learning for medical diagnosis"},
            {"id": "2", "text": "deep learning neural networks"},
            {"id": "3", "text": "clinical trial randomized controlled"},
        ]

        index.add_documents(documents)

        assert index.document_count == 3

    def test_bm25_search(self):
        """Test BM25 search."""
        from jarvis_core.embeddings import BM25Index

        index = BM25Index()

        documents = [
            {"id": "1", "text": "machine learning for medical diagnosis"},
            {"id": "2", "text": "deep learning neural networks image classification"},
            {"id": "3", "text": "clinical trial randomized controlled study"},
        ]

        index.add_documents(documents)

        results = index.search("machine learning", top_k=2)

        assert len(results) <= 2
        assert results[0]["id"] == "1"  # Most relevant

    def test_bm25_empty_query(self):
        """Test BM25 with empty query."""
        from jarvis_core.embeddings import BM25Index

        index = BM25Index()
        index.add_documents([{"id": "1", "text": "test document"}])

        results = index.search("", top_k=5)

        assert len(results) == 0 or results[0]["score"] == 0


class TestSentenceTransformerEmbedding:
    """Tests for Sentence Transformer embeddings."""

    def test_embedding_initialization(self):
        """Test SentenceTransformerEmbedding initialization."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding

        embedder = SentenceTransformerEmbedding()
        assert embedder is not None

    def test_embed_single_text(self):
        """Test embedding single text."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding

        embedder = SentenceTransformerEmbedding()

        embedding = embedder.embed("This is a test sentence.")

        assert isinstance(embedding, np.ndarray)
        assert embedding.ndim == 1
        assert len(embedding) > 0

    def test_embed_batch(self):
        """Test embedding batch of texts."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding

        embedder = SentenceTransformerEmbedding()

        texts = [
            "First document about machine learning",
            "Second document about clinical trials",
            "Third document about data analysis",
        ]

        embeddings = embedder.embed_batch(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 3

    def test_embedding_similarity(self):
        """Test embedding similarity."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding

        embedder = SentenceTransformerEmbedding()

        emb1 = embedder.embed("machine learning")
        emb2 = embedder.embed("artificial intelligence")
        emb3 = embedder.embed("cooking recipes")

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

    def test_hybrid_search_add_documents(self):
        """Test adding documents to hybrid search."""
        from jarvis_core.embeddings import HybridSearch

        search = HybridSearch()

        documents = [
            {"id": "1", "text": "machine learning medical", "title": "ML in Medicine"},
            {"id": "2", "text": "deep learning vision", "title": "Computer Vision"},
        ]

        search.add_documents(documents)

        assert search.document_count == 2

    def test_hybrid_search_query(self):
        """Test hybrid search query."""
        from jarvis_core.embeddings import HybridSearch

        search = HybridSearch()

        documents = [
            {"id": "1", "text": "machine learning for medical diagnosis treatment"},
            {"id": "2", "text": "deep learning computer vision image"},
            {"id": "3", "text": "clinical trial drug efficacy randomized"},
        ]

        search.add_documents(documents)

        results = search.search("machine learning medical", top_k=2)

        assert len(results) <= 2
        assert results[0]["id"] == "1"

    def test_hybrid_search_rrf_fusion(self):
        """Test RRF fusion method."""
        from jarvis_core.embeddings import FusionMethod, HybridSearch

        search = HybridSearch(fusion_method=FusionMethod.RRF)

        documents = [
            {"id": "1", "text": "cancer treatment chemotherapy"},
            {"id": "2", "text": "cancer diagnosis machine learning"},
            {"id": "3", "text": "heart disease prevention"},
        ]

        search.add_documents(documents)

        results = search.search("cancer machine learning", top_k=3)

        # Document 2 should rank high (matches both cancer and ML)
        top_ids = [r["id"] for r in results[:2]]
        assert "2" in top_ids

    def test_hybrid_search_weights(self):
        """Test hybrid search with custom weights."""
        from jarvis_core.embeddings import HybridSearch

        # Emphasize BM25 (keyword matching)
        search_bm25_heavy = HybridSearch(bm25_weight=0.8, embedding_weight=0.2)

        # Emphasize embeddings (semantic matching)
        search_emb_heavy = HybridSearch(bm25_weight=0.2, embedding_weight=0.8)

        documents = [
            {"id": "1", "text": "randomized controlled trial RCT"},
            {"id": "2", "text": "experimental study with random assignment"},
        ]

        search_bm25_heavy.add_documents(documents)
        search_emb_heavy.add_documents(documents)

        # Query with exact keyword
        results_bm25 = search_bm25_heavy.search("RCT", top_k=2)
        # Also test embedding-heavy search (result not validated but ensures no crash)
        _ = search_emb_heavy.search("RCT", top_k=2)

        # BM25-heavy should prefer exact match
        assert results_bm25[0]["id"] == "1"


class TestFusionMethod:
    """Tests for fusion methods."""

    def test_fusion_method_enum(self):
        """Test FusionMethod enum."""
        from jarvis_core.embeddings import FusionMethod

        assert FusionMethod.RRF.value == "rrf"
        assert FusionMethod.LINEAR.value == "linear"
        assert FusionMethod.WEIGHTED.value == "weighted"


class TestSPECTER2:
    """Tests for SPECTER2 scientific embeddings."""

    def test_specter2_initialization(self):
        """Test SPECTER2Embedding initialization."""
        from jarvis_core.embeddings import SPECTER2Embedding

        embedder = SPECTER2Embedding()
        assert embedder is not None

    def test_specter2_embed(self):
        """Test SPECTER2 embedding."""
        from jarvis_core.embeddings import SPECTER2Embedding

        embedder = SPECTER2Embedding()

        embedding = embedder.embed(
            title="A randomized controlled trial of aspirin",
            abstract="Methods: We conducted a double-blind RCT..."
        )

        assert isinstance(embedding, np.ndarray)
        assert embedding.ndim == 1


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
