"""Tests for SourceAdapter, Chunker, and Evidence ingestion pipeline.

Per RP6, this tests the "standard entry point" for populating
EvidenceStore with real content.
"""

from jarvis_core.evidence import EvidenceStore
from jarvis_core.sources import (
    Chunker,
    ChunkResult,
    ExecutionContext,
    SourceDocument,
    ingest,
)
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


class TestChunker:
    """Tests for the Chunker class."""

    def test_empty_text_returns_empty_list(self):
        """Empty text should return no chunks."""
        chunker = Chunker()
        assert chunker.split("") == []
        assert chunker.split("   ") == []

    def test_short_text_returns_single_chunk(self):
        """Text shorter than chunk_size should return single chunk."""
        chunker = Chunker(chunk_size=1000)
        text = "This is a short text."
        chunks = chunker.split(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_splits_into_multiple_chunks(self):
        """Long text should be split into multiple chunks."""
        chunker = Chunker(chunk_size=100, overlap=10)
        # Create text with ~300 chars
        text = "A" * 300
        chunks = chunker.split(text)
        assert len(chunks) > 1

    def test_sentence_boundary_respected(self):
        """Chunker should try to break at sentence boundaries."""
        chunker = Chunker(chunk_size=100, overlap=10)
        text = (
            "First sentence here. Second sentence follows. "
            "Third sentence comes next. Fourth and final."
        )
        chunks = chunker.split(text)
        # At least one chunk should end with a sentence boundary
        assert any(c.endswith(".") for c in chunks)


class TestIngest:
    """Tests for the ingest function."""

    def test_ingest_creates_chunks_in_store(self):
        """Ingest should create chunks in EvidenceStore."""
        store = EvidenceStore()
        doc = SourceDocument(
            source="local",
            locator_base="file:test.txt",
            text="Content of the test file.",
        )

        results = ingest(doc, store)

        assert len(results) == 1
        assert store.has_chunk(results[0].chunk_id)

    def test_ingest_long_document_creates_multiple_chunks(self):
        """Ingest of long document should create multiple chunks."""
        store = EvidenceStore()
        # Create long text (>1000 chars)
        text = "Test sentence. " * 100  # ~1500 chars
        doc = SourceDocument(
            source="pdf",
            locator_base="pdf:document.pdf",
            text=text,
        )

        results = ingest(doc, store)

        assert len(results) > 1
        for result in results:
            assert store.has_chunk(result.chunk_id)

    def test_ingest_locator_format(self):
        """Ingest should create locators with chunk index."""
        store = EvidenceStore()
        text = "A" * 2500  # Will create multiple chunks
        doc = SourceDocument(
            source="url",
            locator_base="url:https://example.com",
            text=text,
        )

        results = ingest(doc, store)

        for i, result in enumerate(results):
            assert result.locator == f"url:https://example.com#chunk:{i}"

    def test_ingest_preserves_source(self):
        """Ingest should preserve source type in chunks."""
        store = EvidenceStore()
        doc = SourceDocument(
            source="pdf",
            locator_base="pdf:paper.pdf",
            text="Paper content here.",
        )

        results = ingest(doc, store)

        chunk = store.get_chunk(results[0].chunk_id)
        assert chunk is not None
        assert chunk.source == "pdf"

    def test_ingest_creates_previews(self):
        """Ingest should create preview text for each chunk."""
        store = EvidenceStore()
        long_text = "A" * 500
        doc = SourceDocument(
            source="local",
            locator_base="file:test.txt",
            text=long_text,
        )

        results = ingest(doc, store, preview_length=50)

        assert len(results[0].preview) <= 53  # 50 + "..."
        assert results[0].preview.endswith("...")


class TestExecutionContext:
    """Tests for ExecutionContext."""

    def test_add_chunks_and_get_ids(self):
        """ExecutionContext should track available chunks."""
        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        chunk_id = store.add_chunk("local", "file:test.txt", "content")
        result = ChunkResult(
            chunk_id=chunk_id,
            locator="file:test.txt#chunk:0",
            preview="content",
        )

        ctx.add_chunks([result])

        assert chunk_id in ctx.get_chunk_ids()

    def test_get_chunks_preview(self):
        """ExecutionContext should provide preview for prompts."""
        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        chunk_id = store.add_chunk("pdf", "pdf:test.pdf", "PDF content")
        result = ChunkResult(
            chunk_id=chunk_id,
            locator="pdf:test.pdf#chunk:0",
            preview="PDF content",
        )

        ctx.add_chunks([result])
        previews = ctx.get_chunks_preview()

        assert len(previews) == 1
        assert previews[0]["chunk_id"] == chunk_id
        assert previews[0]["locator"] == "pdf:test.pdf#chunk:0"
        assert previews[0]["preview"] == "PDF content"


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_ingest_and_context(self):
        """Full pipeline: ingest document, add to context, verify access."""
        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        doc = SourceDocument(
            source="pdf",
            locator_base="pdf:research_paper.pdf",
            text="CD73 is expressed on regulatory T cells. " * 50,
        )

        results = ingest(doc, store)
        ctx.add_chunks(results)

        # All ingested chunks should be in store
        for result in results:
            assert store.has_chunk(result.chunk_id)

        # Context should have all chunk_ids
        assert len(ctx.get_chunk_ids()) == len(results)

        # Previews should be available for agent prompts
        previews = ctx.get_chunks_preview()
        assert len(previews) == len(results)