"""Tests for Local Embedding and Hybrid Retrieval.

Tests for Task 1.2: ローカル埋め込み
"""
import pytest


class TestLocalEmbedProvider:
    """Tests for LocalEmbedProvider."""

    def test_provider_init_default(self):
        """Test default provider initialization."""
        from jarvis_core.providers.local_embed import LocalEmbedProvider

        provider = LocalEmbedProvider()
        assert provider.model_name == "all-MiniLM-L6-v2"
        assert provider.dimension == 384

    def test_provider_for_scientific(self):
        """Test scientific paper embedding provider."""
        from jarvis_core.providers.local_embed import LocalEmbedProvider

        provider = LocalEmbedProvider.for_scientific()
        assert provider.model_name == "allenai/specter2"
        assert provider.dimension == 768
        assert provider.model_info["use_case"] == "scientific"

    def test_provider_for_multilingual(self):
        """Test multilingual embedding provider."""
        from jarvis_core.providers.local_embed import LocalEmbedProvider

        provider = LocalEmbedProvider.for_multilingual()
        assert "multilingual" in provider.model_name.lower()

    def test_provider_model_config(self):
        """Test model configuration."""
        from jarvis_core.providers.local_embed import (
            MODEL_CONFIG,
            EmbeddingModel,
        )

        for model in EmbeddingModel:
            assert model in MODEL_CONFIG
            config = MODEL_CONFIG[model]
            assert "dimension" in config
            assert "speed" in config
            assert "use_case" in config

    def test_embedding_model_enum(self):
        """Test EmbeddingModel enum values."""
        from jarvis_core.providers.local_embed import EmbeddingModel

        assert EmbeddingModel.MINILM.value == "all-MiniLM-L6-v2"
        assert EmbeddingModel.SPECTER2.value == "allenai/specter2"
        assert EmbeddingModel.MPNET.value == "all-mpnet-base-v2"


class TestHybridRetrieval:
    """Tests for Hybrid Retrieval."""

    def test_retrieval_result_dataclass(self):
        """Test RetrievalResult dataclass."""
        from jarvis_core.retrieval.hybrid_retrieval import RetrievalResult

        result = RetrievalResult(
            doc_id="doc1",
            text="Sample text",
            score=0.95,
            source="hybrid",
        )
        assert result.doc_id == "doc1"
        assert result.score == 0.95
        assert result.source == "hybrid"

    def test_bm25_retriever_init(self):
        """Test BM25Retriever initialization."""
        from jarvis_core.retrieval.hybrid_retrieval import BM25Retriever

        retriever = BM25Retriever(k1=1.5, b=0.75)
        assert retriever.k1 == 1.5
        assert retriever.b == 0.75

    def test_bm25_index_and_search(self):
        """Test BM25 indexing and search."""
        pytest.importorskip("rank_bm25")
        from jarvis_core.retrieval.hybrid_retrieval import BM25Retriever

        documents = [
            {"id": "1", "text": "machine learning algorithms"},
            {"id": "2", "text": "deep learning neural networks"},
            {"id": "3", "text": "natural language processing"},
        ]

        retriever = BM25Retriever()
        retriever.index(documents)

        results = retriever.search("deep learning", top_k=2)
        assert len(results) > 0
        # First result should be document about deep learning
        assert results[0][0] == "2"

    def test_dense_retriever_init(self):
        """Test DenseRetriever initialization."""
        from jarvis_core.retrieval.hybrid_retrieval import DenseRetriever

        retriever = DenseRetriever(model_name="all-MiniLM-L6-v2")
        assert retriever.model_name == "all-MiniLM-L6-v2"

    def test_hybrid_retriever_init(self):
        """Test HybridRetriever initialization."""
        from jarvis_core.retrieval.hybrid_retrieval import HybridRetriever

        retriever = HybridRetriever(
            bm25_weight=0.4,
            dense_weight=0.6,
        )
        assert retriever.bm25_weight == 0.4
        assert retriever.dense_weight == 0.6

    def test_rrf_fusion_ranking(self):
        """Test RRF fusion produces correct ranking."""
        from jarvis_core.retrieval.hybrid_retrieval import HybridRetriever

        retriever = HybridRetriever()

        # Simulate results where doc1 appears in both lists
        bm25_results = [("doc1", 10.0), ("doc2", 8.0), ("doc3", 6.0)]
        dense_results = [("doc1", 0.95), ("doc4", 0.90), ("doc2", 0.85)]

        combined = retriever._rrf_fusion(bm25_results, dense_results)

        # doc1 should be ranked first (appears in both)
        assert combined[0][0] == "doc1"

    def test_create_hybrid_retriever_factory(self):
        """Test create_hybrid_retriever factory function."""
        from jarvis_core.retrieval.hybrid_retrieval import create_hybrid_retriever

        documents = [
            {"id": "1", "text": "test document"},
        ]

        retriever = create_hybrid_retriever(documents)
        assert retriever is not None
        assert "1" in retriever._documents


class TestContextualEmbeddings:
    """Tests for Contextual Embeddings."""

    def test_contextual_chunk_dataclass(self):
        """Test ContextualChunk dataclass."""
        from jarvis_core.retrieval.contextual_embeddings import ContextualChunk

        chunk = ContextualChunk(
            chunk_id="c1",
            text="Main content",
            context_prefix="Methods",
            context_suffix="Next sentence",
            metadata={"page": 1},
        )
        assert chunk.chunk_id == "c1"
        assert chunk.context_prefix == "Methods"

    def test_contextual_embedder_prepare_text(self):
        """Test contextual text preparation."""
        from jarvis_core.retrieval.contextual_embeddings import ContextualChunk, ContextualEmbedder

        embedder = ContextualEmbedder(
            include_section=True,
            include_metadata=True,
        )

        chunk = ContextualChunk(
            chunk_id="c1",
            text="The results show significant improvement",
            context_prefix="Results",
            context_suffix="This confirms our hypothesis",
            metadata={},
        )

        text = embedder.prepare_contextual_text(
            chunk,
            paper_metadata={"year": "2024", "journal": "Nature"},
        )

        assert "2024" in text
        assert "Nature" in text
        assert "Results" in text
        assert "significant improvement" in text
