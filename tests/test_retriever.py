"""Tests for BM25 Retriever.

Per RP9, tests that relevant chunks are returned for queries.
"""

from jarvis_core.evidence import EvidenceStore
from jarvis_core.retriever import (
    BM25Retriever,
    get_relevant_chunks,
    tokenize,
)
from jarvis_core.sources import ChunkResult, ExecutionContext, SourceDocument, ingest
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


class TestTokenize:
    """Tests for tokenizer."""

    def test_tokenize_english(self):
        """Should tokenize English text."""
        tokens = tokenize("Hello world, this is a test!")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens

    def test_tokenize_removes_short(self):
        """Should remove very short tokens."""
        tokens = tokenize("I am a test")
        assert "i" not in tokens  # Too short
        assert "am" in tokens
        assert "test" in tokens

    def test_tokenize_japanese(self):
        """Should handle Japanese text."""
        tokens = tokenize("これはテストです")
        assert len(tokens) > 0

class TestBM25Retriever:
    """Tests for BM25Retriever."""

    def setup_method(self):
        """Set up test data."""
        self.store = EvidenceStore()

        # Create test documents about different topics
        self.docs = [
            ("CD73 is expressed on regulatory T cells and adenosine signaling.", "doc1"),
            ("Machine learning uses neural networks for prediction.", "doc2"),
            ("Immune checkpoint inhibitors target PD-1 and CTLA-4.", "doc3"),
            ("Python programming language is popular for data science.", "doc4"),
            ("Adenosine pathway affects tumor microenvironment.", "doc5"),
        ]

        self.chunks = []
        for text, name in self.docs:
            chunk_id = self.store.add_chunk("test", f"test:{name}", text)
            self.chunks.append(
                ChunkResult(
                    chunk_id=chunk_id,
                    locator=f"test:{name}#chunk:0",
                    preview=text[:50],
                )
            )

    def test_build_creates_index(self):
        """Should build index from chunks."""
        retriever = BM25Retriever().build(self.chunks, self.store)
        assert len(retriever) == 5

    def test_search_returns_relevant(self):
        """Should return relevant chunks for query."""
        retriever = BM25Retriever().build(self.chunks, self.store)

        results = retriever.search("CD73 adenosine T cells", k=3)

        # Should find the adenosine-related docs
        chunk_ids = [r.chunk_id for r in results]
        assert len(results) <= 3

        # The CD73 and adenosine docs should rank high
        # Get the chunks and check content
        top_texts = [self.store.get_chunk(cid).text for cid in chunk_ids]
        assert any("CD73" in t or "adenosine" in t for t in top_texts)

    def test_search_respects_k_limit(self):
        """Should return at most k results."""
        retriever = BM25Retriever().build(self.chunks, self.store)

        results = retriever.search("test query", k=2)
        assert len(results) <= 2

    def test_search_empty_query(self):
        """Should return empty for empty query."""
        retriever = BM25Retriever().build(self.chunks, self.store)

        results = retriever.search("", k=3)
        assert len(results) == 0

    def test_search_returns_valid_chunk_ids(self):
        """Should only return chunk_ids that exist in store."""
        retriever = BM25Retriever().build(self.chunks, self.store)

        results = retriever.search("machine learning python", k=5)

        for result in results:
            assert self.store.has_chunk(result.chunk_id)

class TestGetRelevantChunks:
    """Tests for convenience function."""

    def test_returns_all_when_few_chunks(self):
        """Should return all chunks when below threshold."""
        store = EvidenceStore()
        chunks = []
        for i in range(5):
            chunk_id = store.add_chunk("test", f"test:{i}", f"Content {i}")
            chunks.append(
                ChunkResult(chunk_id=chunk_id, locator=f"test:{i}", preview=f"Content {i}")
            )

        results = get_relevant_chunks(
            "query",
            chunks,
            store,
            k=3,
            min_chunks_for_retrieval=10,
        )

        # Should return up to k (3) even though we have 5
        assert len(results) <= 3

    def test_uses_retrieval_when_many_chunks(self):
        """Should use BM25 when above threshold."""
        store = EvidenceStore()
        chunks = []

        # Create many chunks about different topics
        topics = ["cancer research", "machine learning", "immune system", "data science"]
        for i in range(25):
            topic = topics[i % len(topics)]
            text = f"This is document {i} about {topic} with detailed information."
            chunk_id = store.add_chunk("test", f"test:{i}", text)
            chunks.append(ChunkResult(chunk_id=chunk_id, locator=f"test:{i}", preview=text[:30]))

        results = get_relevant_chunks(
            "machine learning data",
            chunks,
            store,
            k=5,
            min_chunks_for_retrieval=20,
        )

        assert len(results) <= 5
        # All returned chunks should be valid
        for r in results:
            assert store.has_chunk(r.chunk_id)

class TestExecutionContextRetrieval:
    """Tests for ExecutionContext retrieval integration."""

    def test_get_relevant_chunks(self):
        """Should retrieve relevant chunks from context."""
        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        # Add some chunks
        for i in range(5):
            chunk_id = store.add_chunk("test", f"test:{i}", f"Topic {i} content")
            ctx.add_chunks(
                [ChunkResult(chunk_id=chunk_id, locator=f"test:{i}", preview=f"Topic {i}")]
            )

        results = ctx.get_relevant_chunks("topic", k=3)
        assert len(results) <= 3

    def test_get_relevant_chunks_preview(self):
        """Should return preview format for agent."""
        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        chunk_id = store.add_chunk("test", "test:0", "Test content")
        ctx.add_chunks([ChunkResult(chunk_id=chunk_id, locator="test:0", preview="Test")])

        previews = ctx.get_relevant_chunks_preview("test", k=5)
        assert len(previews) == 1
        assert "chunk_id" in previews[0]
        assert "locator" in previews[0]
        assert "preview" in previews[0]

class TestIntegration:
    """Integration tests for full retrieval pipeline."""

    def test_ingest_and_retrieve(self):
        """Should ingest documents and retrieve relevant chunks."""
        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        # Ingest multiple documents about different topics
        docs = [
            SourceDocument(
                source="test",
                locator_base="test:immunology",
                text="CD73 is an ectoenzyme that produces adenosine. "
                "It is expressed on regulatory T cells and affects immune responses.",
            ),
            SourceDocument(
                source="test",
                locator_base="test:ml",
                text="Machine learning algorithms learn from data. "
                "Neural networks are a type of machine learning model.",
            ),
            SourceDocument(
                source="test",
                locator_base="test:cancer",
                text="Tumor microenvironment includes various immune cells. "
                "Adenosine signaling can suppress anti-tumor immunity.",
            ),
        ]

        for doc in docs:
            results = ingest(doc, store)
            ctx.add_chunks(results)

        # Query for adenosine-related content
        relevant = ctx.get_relevant_chunks("adenosine immune cells", k=3)

        # Should find the immunology and cancer docs
        assert len(relevant) > 0

        # Check that relevant chunks contain expected content
        relevant_texts = [store.get_chunk(r.chunk_id).text for r in relevant]
        assert any("adenosine" in t.lower() for t in relevant_texts)
