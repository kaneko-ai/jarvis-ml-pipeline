"""Tests for the new embeddings module.

Per JARVIS_COMPLETION_PLAN_v3 Task 1.2
"""

import tempfile
from pathlib import Path

import pytest
import numpy as np


class TestSentenceTransformerEmbedding:
    """Tests for SentenceTransformerEmbedding."""

    def test_init_default(self):
        """Test default initialization."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding
        
        embedder = SentenceTransformerEmbedding()
        assert embedder.model_name == "all-MiniLM-L6-v2"
        assert embedder.dimension == 384

    def test_init_with_model_enum(self):
        """Test initialization with EmbeddingModel enum."""
        from jarvis_core.embeddings.sentence_transformer import (
            SentenceTransformerEmbedding,
            EmbeddingModel,
        )
        
        embedder = SentenceTransformerEmbedding(model_name=EmbeddingModel.SPECTER2)
        assert embedder.model_name == "allenai/specter2"
        assert embedder.dimension == 768

    def test_factory_methods(self):
        """Test factory methods."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding
        
        scientific = SentenceTransformerEmbedding.for_scientific()
        assert scientific.model_name == "allenai/specter2"
        
        multilingual = SentenceTransformerEmbedding.for_multilingual()
        assert "multilingual" in multilingual.model_name.lower()
        
        general = SentenceTransformerEmbedding.for_general()
        assert general.model_name == "all-MiniLM-L6-v2"

    def test_encode_fallback(self):
        """Test encoding with hash fallback when model unavailable."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding
        
        embedder = SentenceTransformerEmbedding()
        # Force hash fallback by not initializing the model
        vectors = embedder._hash_embeddings(["test text", "another text"])
        
        assert vectors.shape == (2, 384)
        # Vectors should be normalized
        norms = np.linalg.norm(vectors, axis=1)
        assert np.allclose(norms, 1.0, atol=0.01)

    def test_encode_single_text(self):
        """Test encoding a single text."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding
        
        embedder = SentenceTransformerEmbedding()
        vectors = embedder.encode("Hello world")
        
        assert vectors.shape == (1, embedder.dimension)


class TestBM25Index:
    """Tests for BM25Index."""

    def test_init(self):
        """Test default initialization."""
        from jarvis_core.embeddings import BM25Index
        
        index = BM25Index()
        assert index.doc_count == 0

    def test_build_and_search(self):
        """Test building and searching the index."""
        pytest.importorskip("rank_bm25")
        from jarvis_core.embeddings import BM25Index
        
        corpus = [
            "machine learning algorithms",
            "deep learning neural networks",
            "natural language processing",
        ]
        
        index = BM25Index()
        index.build(corpus, ids=["doc1", "doc2", "doc3"])
        
        assert index.doc_count == 3
        
        results = index.search("deep learning", top_k=2)
        assert len(results) > 0
        assert results[0][0] == "doc2"  # Should match "deep learning" doc

    def test_save_and_load(self):
        """Test saving and loading the index."""
        pytest.importorskip("rank_bm25")
        from jarvis_core.embeddings import BM25Index
        
        corpus = ["test document one", "test document two"]
        index = BM25Index()
        index.build(corpus, ids=["d1", "d2"])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bm25.pkl"
            index.save(path)
            
            loaded = BM25Index.load(path)
            assert loaded.doc_count == 2
            
            results = loaded.search("document", top_k=2)
            assert len(results) == 2

    def test_add_document(self):
        """Test adding a document."""
        pytest.importorskip("rank_bm25")
        from jarvis_core.embeddings import BM25Index
        
        index = BM25Index()
        index.build(["initial doc"], ids=["d1"])
        
        index.add_document("d2", "added document")
        assert index.doc_count == 2
        assert index.get_document("d2") == "added document"


class TestHybridSearch:
    """Tests for HybridSearch."""

    def test_init(self):
        """Test default initialization."""
        from jarvis_core.embeddings import HybridSearch
        
        hybrid = HybridSearch()
        assert hybrid.doc_count == 0

    def test_index_and_search(self):
        """Test indexing and searching."""
        pytest.importorskip("rank_bm25")
        from jarvis_core.embeddings import HybridSearch
        
        corpus = [
            "machine learning algorithms for data science",
            "deep learning with neural networks",
            "natural language processing and NLP",
        ]
        
        hybrid = HybridSearch()
        hybrid.index(corpus, ids=["d1", "d2", "d3"])
        
        assert hybrid.doc_count == 3
        
        # Test hybrid search
        results = hybrid.search("machine learning", top_k=2, mode="hybrid")
        assert len(results.results) > 0
        assert results.results[0].doc_id == "d1"
        assert results.fusion_method == "rrf"

    def test_search_modes(self):
        """Test different search modes."""
        pytest.importorskip("rank_bm25")
        from jarvis_core.embeddings import HybridSearch
        
        corpus = ["machine learning", "deep learning"]
        hybrid = HybridSearch()
        hybrid.index(corpus, ids=["d1", "d2"])
        
        # Sparse only
        sparse_results = hybrid.search("machine", mode="sparse")
        assert sparse_results.fusion_method == "sparse"
        
        # Dense only
        dense_results = hybrid.search("machine", mode="dense")
        assert dense_results.fusion_method == "dense"

    def test_rrf_fusion(self):
        """Test RRF fusion logic."""
        from jarvis_core.embeddings import HybridSearch, FusionMethod
        
        hybrid = HybridSearch(fusion_method=FusionMethod.RRF)
        
        sparse = {"d1": 10.0, "d2": 8.0, "d3": 6.0}
        dense = {"d1": 0.95, "d4": 0.90, "d2": 0.85}
        
        combined = hybrid._rrf_fusion(sparse, dense)
        
        # d1 appears in both, should be ranked first
        assert combined[0][0] == "d1"

    def test_linear_fusion(self):
        """Test linear fusion logic."""
        from jarvis_core.embeddings import HybridSearch, FusionMethod
        
        hybrid = HybridSearch(
            fusion_method=FusionMethod.LINEAR,
            dense_weight=0.6,
            sparse_weight=0.4,
        )
        
        sparse = {"d1": 1.0, "d2": 0.5}
        dense = {"d1": 0.8, "d2": 1.0}
        
        combined = hybrid._linear_fusion(sparse, dense)
        
        # Results should be ranked by weighted combination
        assert len(combined) == 2

    def test_save_and_load(self):
        """Test saving and loading."""
        pytest.importorskip("rank_bm25")
        from jarvis_core.embeddings import HybridSearch
        
        corpus = ["test doc one", "test doc two"]
        hybrid = HybridSearch()
        hybrid.index(corpus, ids=["d1", "d2"])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "hybrid"
            hybrid.save(path)
            
            loaded = HybridSearch.load(path)
            assert loaded.doc_count == 2
            
            results = loaded.search("test", top_k=2)
            assert len(results.results) == 2

    def test_with_metadata(self):
        """Test indexing with metadata."""
        pytest.importorskip("rank_bm25")
        from jarvis_core.embeddings import HybridSearch
        
        corpus = ["doc one", "doc two"]
        metadata = [{"source": "arxiv"}, {"source": "pubmed"}]
        
        hybrid = HybridSearch()
        hybrid.index(corpus, ids=["d1", "d2"], metadata=metadata)
        
        results = hybrid.search("doc", top_k=2)
        assert results.results[0].metadata.get("source") in ["arxiv", "pubmed"]


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.embeddings import (
            SentenceTransformerEmbedding,
            get_default_embedding_model,
            BM25Index,
            HybridSearch,
            FusionMethod,
        )
        
        assert SentenceTransformerEmbedding is not None
        assert get_default_embedding_model is not None
        assert BM25Index is not None
        assert HybridSearch is not None
        assert FusionMethod is not None

    def test_get_default_model(self):
        """Test get_default_embedding_model."""
        from jarvis_core.embeddings import get_default_embedding_model
        
        model = get_default_embedding_model()
        assert model.model_name == "all-MiniLM-L6-v2"
