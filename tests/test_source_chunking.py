
import pytest
from unittest.mock import MagicMock
from jarvis_core.sources.chunking import Chunker, SourceDocument, ingest, ChunkResult, ExecutionContext
from jarvis_core.evidence import EvidenceStore

class TestChunker:
    def test_chunker_init(self):
        chunker = Chunker(chunk_size=500, overlap=50)
        assert chunker.chunk_size == 500
        assert chunker.overlap == 50

    def test_split_simple_text(self):
        text = "Hello world. " * 50
        chunker = Chunker(chunk_size=100, overlap=10)
        chunks = chunker.split(text)
        assert len(chunks) > 0
        assert all(len(c) <= 100 for c in chunks)

    def test_split_empty_text(self):
        chunker = Chunker()
        assert chunker.split("") == []
        assert chunker.split("   ") == []

    def test_sentence_boundary_handling(self):
        # Create text where rigid split would cut a sentence, but boundary search should fix it
        # 80 chars + sentence end + more chars
        text = "A" * 80 + ". Next sentence."
        chunker = Chunker(chunk_size=90, overlap=0)
        chunks = chunker.split(text)
        # Should split at '.', so first chunk is 81 chars
        assert len(chunks) >= 1
        assert chunks[0].endswith(".")

class TestIngest:
    def test_ingest_flow(self):
        mock_store = MagicMock(spec=EvidenceStore)
        mock_store.add_chunk.side_effect = ["id1", "id2"]
        
        doc = SourceDocument(
            source="local",
            locator_base="file:///test.txt",
            text="Chunk one. Chunk two."
        )
        
        # Force small chunks to ensure multiple
        chunker = Chunker(chunk_size=15, overlap=0)
        
        results = ingest(document=doc, store=mock_store, chunker=chunker)
        
        assert len(results) >= 2
        assert mock_store.add_chunk.call_count >= 2
        assert isinstance(results[0], ChunkResult)
        assert results[0].chunk_id == "id1"
        assert "chunk:0" in results[0].locator

class TestExecutionContext:
    def test_available_chunks(self):
        mock_store = MagicMock(spec=EvidenceStore)
        context = ExecutionContext(evidence_store=mock_store)
        
        chunks = [
            ChunkResult(chunk_id="1", locator="loc1", preview="p1"),
            ChunkResult(chunk_id="2", locator="loc2", preview="p2")
        ]
        context.add_chunks(chunks)
        
        assert len(context.available_chunks) == 2
        assert context.get_chunk_ids() == ["1", "2"]
        
        previews = context.get_chunks_preview()
        assert len(previews) == 2
        assert previews[0]["chunk_id"] == "1"
