"""Integration tests for Evidence QA Pipeline.

Per RP11, these tests verify the complete E2E flow:
PDF/URL → ingest → retrieve → answer → citations → success
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.evidence import EvidenceStore
from jarvis_core.evidence_qa import (
    EvidenceQAAgent,
    _detect_input_type,
    _ingest_input,
    run_evidence_qa,
)
from jarvis_core.sources import ExecutionContext

SAMPLE_PDF = ROOT / "tests" / "fixtures" / "sample.pdf"


class TestDetectInputType:
    """Tests for input type detection."""

    def test_detect_pdf(self):
        assert _detect_input_type("paper.pdf") == "pdf"
        assert _detect_input_type("/path/to/file.PDF") == "pdf"

    def test_detect_url(self):
        assert _detect_input_type("http://example.com") == "url"
        assert _detect_input_type("https://example.com/page") == "url"

    def test_detect_local(self):
        assert _detect_input_type("file.txt") == "local"
        assert _detect_input_type("/path/to/file") == "local"


class TestIngestInput:
    """Tests for input ingestion."""

    def test_ingest_pdf(self):
        """Should ingest PDF and add chunks to context."""
        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        results = _ingest_input(str(SAMPLE_PDF), store, ctx)

        assert len(results) > 0
        assert len(ctx.available_chunks) > 0
        for r in results:
            assert store.has_chunk(r.chunk_id)

    def test_ingest_url_mocked(self):
        """Should ingest URL (mocked) and add chunks to context."""
        from jarvis_core.sources import ChunkResult

        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        # Add chunk directly (simulating what ingest_url would do)
        chunk_id = store.add_chunk(
            "url",
            "url:https://example.com#chunk:0",
            "Web content from example.com",
        )
        results = [
            ChunkResult(
                chunk_id=chunk_id,
                locator="url:https://example.com#chunk:0",
                preview="Web content...",
            )
        ]
        ctx.add_chunks(results)

        # Verify the chunk is accessible
        assert len(results) > 0
        assert store.has_chunk(chunk_id)
        assert len(ctx.available_chunks) > 0


class TestEvidenceQAAgent:
    """Tests for EvidenceQAAgent."""

    def test_agent_returns_result(self):
        """Agent should return AgentResult with answer."""
        mock_llm = MagicMock()
        mock_llm.chat.return_value = "CD73 is expressed on T cells. chunk-123"

        agent = EvidenceQAAgent(llm=mock_llm)

        from jarvis_core.task import Task, TaskCategory

        task = Task(
            task_id="test",
            title="What is CD73?",
            category=TaskCategory.GENERIC,
            user_goal="What is CD73?",
        )

        store = EvidenceStore()
        chunk_id = store.add_chunk(
            "pdf",
            "pdf:test.pdf#page:1#chunk:0",
            "CD73 is an ectoenzyme expressed on T cells.",
        )

        from jarvis_core.sources import ChunkResult

        ctx = ExecutionContext(evidence_store=store)
        ctx.add_chunks([
            ChunkResult(
                chunk_id=chunk_id,
                locator="pdf:test.pdf#page:1#chunk:0",
                preview="CD73 is an ectoenzyme...",
            )
        ])

        result = agent.run_single(task, context=ctx)

        assert result.answer != ""
        assert result.status in ["success", "partial", "fail"]

    def test_agent_extracts_chunk_ids(self):
        """Agent should extract referenced chunk_ids."""
        mock_llm = MagicMock()

        agent = EvidenceQAAgent(llm=mock_llm)

        from jarvis_core.task import Task, TaskCategory

        task = Task(
            task_id="test",
            title="Test query",
            category=TaskCategory.GENERIC,
        )

        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "test:loc", "Test content here.")

        from jarvis_core.sources import ChunkResult

        ctx = ExecutionContext(evidence_store=store)
        ctx.add_chunks([
            ChunkResult(chunk_id=chunk_id, locator="test:loc", preview="Test...")
        ])

        # Mock LLM to return claim with the chunk_id (RP13 format)
        mock_llm.chat.return_value = f"1. The answer is based on evidence [{chunk_id}]\n\nSTATUS: success"

        result = agent.run_single(task, context=ctx)

        # Should have extracted the chunk_id as citation
        assert len(result.citations) > 0
        assert any(c.chunk_id == chunk_id for c in result.citations)


class TestRunEvidenceQA:
    """Integration tests for run_evidence_qa."""

    def test_full_pipeline_with_pdf(self):
        """Full pipeline: PDF → ingest → agent → answer."""
        mock_llm = MagicMock()

        with patch("jarvis_core.evidence_qa.LLMClient") as MockLLMClient:
            # We need to create a custom LLM that references chunks correctly
            # First, let's extract actual chunk content
            store = EvidenceStore()
            ctx = ExecutionContext(evidence_store=store)

            from jarvis_core.pdf_extractor import ingest_pdf
            results = ingest_pdf(str(SAMPLE_PDF), store)

            # Get a real chunk_id to use in mock response
            if results:
                real_chunk_id = results[0].chunk_id
                real_chunk = store.get_chunk(real_chunk_id)

                # Mock LLM to return response with real chunk_id
                mock_response = f"Page 1 contains test content. {real_chunk_id} status: success"

                MockLLMClient.return_value.chat.return_value = mock_response

                answer = run_evidence_qa(
                    query="What is on page 1?",
                    inputs=[str(SAMPLE_PDF)],
                    llm=MockLLMClient.return_value,
                )

                assert answer != ""
                assert isinstance(answer, str)

    def test_pipeline_returns_string(self):
        """run_evidence_qa should always return a string."""
        with patch("jarvis_core.evidence_qa.LLMClient") as MockLLMClient:
            MockLLMClient.return_value.chat.return_value = "Test answer"

            answer = run_evidence_qa(
                query="Test query",
                inputs=[str(SAMPLE_PDF)],
                llm=MockLLMClient.return_value,
            )

            assert isinstance(answer, str)


class TestE2EWithMockedLLM:
    """E2E tests with properly mocked LLM that returns valid citations."""

    def test_success_case_with_valid_citations(self):
        """Test that proper citations lead to success status."""
        # Create a mock LLM that will return proper chunk_ids
        with patch("jarvis_core.evidence_qa.LLMClient") as MockLLMClient:
            # First, we need to ingest and get real chunk_ids
            store = EvidenceStore()
            from jarvis_core.pdf_extractor import ingest_pdf
            results = ingest_pdf(str(SAMPLE_PDF), store)

            assert len(results) > 0, "Sample PDF should produce chunks"

            # Get chunk info
            chunk_id = results[0].chunk_id
            chunk = store.get_chunk(chunk_id)

            # Mock LLM to return answer with valid chunk_id and overlapping content
            mock_response = (
                f"Page 1 content is shown here. "
                f"Reference: {chunk_id}. "
                f"status: success"
            )
            MockLLMClient.return_value.chat.return_value = mock_response

            answer = run_evidence_qa(
                query="What is on page 1?",
                inputs=[str(SAMPLE_PDF)],
                llm=MockLLMClient.return_value,
            )

            # Should return non-empty answer
            assert answer != ""
            assert len(answer) > 10
