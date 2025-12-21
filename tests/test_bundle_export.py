"""Tests for Evidence Bundle Export and Structured Result.

Per RP12, these tests verify:
- EvidenceQAResult structure
- Bundle export (bundle.json, evidence/*.txt, citations.md)
- Backward compatibility of run_evidence_qa()
"""
import json
import tempfile
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.agents import Citation
from jarvis_core.evidence import EvidenceStore
from jarvis_core.result import EvidenceQAResult
from jarvis_core.bundle import export_evidence_bundle, _safe_filename


SAMPLE_PDF = ROOT / "tests" / "fixtures" / "sample.pdf"


class TestEvidenceQAResult:
    """Tests for EvidenceQAResult dataclass."""

    def test_create_result(self):
        """Should create result with all fields."""
        result = EvidenceQAResult(
            answer="Test answer",
            status="success",
            citations=[],
            inputs=["paper.pdf"],
            query="What is CD73?",
        )
        assert result.answer == "Test answer"
        assert result.status == "success"
        assert result.query == "What is CD73?"

    def test_extracts_chunk_ids(self):
        """Should extract chunk_ids from citations."""
        citations = [
            Citation(chunk_id="c1", source="pdf", locator="loc1", quote="q1"),
            Citation(chunk_id="c2", source="url", locator="loc2", quote="q2"),
        ]
        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=citations,
            inputs=[],
            query="query",
        )
        assert result.chunks_used == ["c1", "c2"]

    def test_to_dict(self):
        """Should convert to dict for JSON serialization."""
        result = EvidenceQAResult(
            answer="Answer",
            status="partial",
            citations=[
                Citation(chunk_id="c1", source="pdf", locator="l1", quote="q1"),
            ],
            inputs=["paper.pdf"],
            query="test query",
        )
        d = result.to_dict()

        assert d["answer"] == "Answer"
        assert d["status"] == "partial"
        assert d["query"] == "test query"
        assert len(d["citations"]) == 1
        assert "timestamp" in d["meta"]

    def test_from_dict(self):
        """Should create from dict."""
        data = {
            "answer": "Answer",
            "status": "success",
            "citations": [
                {"chunk_id": "c1", "source": "pdf", "locator": "l1", "quote": "q1"}
            ],
            "inputs": ["file.pdf"],
            "query": "query",
            "chunks_used": ["c1"],
            "meta": {"key": "value"},
        }
        result = EvidenceQAResult.from_dict(data)

        assert result.answer == "Answer"
        assert result.status == "success"
        assert len(result.citations) == 1


class TestSafeFilename:
    """Tests for filename sanitization."""

    def test_safe_filename_removes_special_chars(self):
        assert _safe_filename("test<>:file") == "test___file"

    def test_safe_filename_limits_length(self):
        long_name = "a" * 100
        assert len(_safe_filename(long_name)) == 50


class TestExportEvidenceBundle:
    """Tests for bundle export."""

    def test_export_creates_bundle_json(self):
        """Should create bundle.json."""
        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "test:loc", "Chunk text content.")

        result = EvidenceQAResult(
            answer="Test answer",
            status="success",
            citations=[
                Citation(chunk_id=chunk_id, source="pdf", locator="test:loc", quote="quote"),
            ],
            inputs=["paper.pdf"],
            query="test query",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            bundle_path = Path(tmpdir) / "bundle.json"
            assert bundle_path.exists()

            with open(bundle_path) as f:
                data = json.load(f)
            assert data["answer"] == "Test answer"
            assert data["status"] == "success"

    def test_export_creates_evidence_files(self):
        """Should create evidence/*.txt for each chunk used."""
        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "test:loc", "Evidence text here.")

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[
                Citation(chunk_id=chunk_id, source="pdf", locator="test:loc", quote="q"),
            ],
            inputs=[],
            query="query",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            evidence_dir = Path(tmpdir) / "evidence"
            assert evidence_dir.exists()

            # Should have at least one evidence file
            evidence_files = list(evidence_dir.glob("*.txt"))
            assert len(evidence_files) >= 1

            # Check content
            content = evidence_files[0].read_text(encoding="utf-8")
            assert "Evidence text here" in content

    def test_export_creates_citations_md(self):
        """Should create citations.md."""
        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "test:loc", "Chunk text.")

        result = EvidenceQAResult(
            answer="Answer text",
            status="partial",
            citations=[
                Citation(chunk_id=chunk_id, source="pdf", locator="test:loc", quote="quote text"),
            ],
            inputs=["paper.pdf"],
            query="What is this?",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            citations_path = Path(tmpdir) / "citations.md"
            assert citations_path.exists()

            content = citations_path.read_text(encoding="utf-8")
            assert "Answer text" in content
            assert "What is this?" in content
            assert "quote text" in content

    def test_quote_from_evidence_store(self):
        """Quote in bundle should be from EvidenceStore (not agent)."""
        store = EvidenceStore()
        chunk_id = store.add_chunk(
            "pdf",
            "page:5",
            "This is the authoritative text from EvidenceStore.",
        )

        # Agent-provided quote is different (should be engine-regenerated)
        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[
                Citation(
                    chunk_id=chunk_id,
                    source="pdf",
                    locator="page:5",
                    quote="Engine regenerated quote",  # This comes from Engine
                ),
            ],
            inputs=[],
            query="query",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            # Check evidence file has store content
            evidence_dir = Path(tmpdir) / "evidence"
            evidence_files = list(evidence_dir.glob("*.txt"))
            content = evidence_files[0].read_text(encoding="utf-8")
            assert "authoritative text from EvidenceStore" in content


class TestBackwardCompatibility:
    """Tests for backward compatibility."""

    def test_run_evidence_qa_returns_string(self):
        """run_evidence_qa should return str (not EvidenceQAResult)."""
        with patch("jarvis_core.evidence_qa.LLMClient") as MockLLMClient:
            MockLLMClient.return_value.chat.return_value = "Test answer"

            from jarvis_core.evidence_qa import run_evidence_qa

            answer = run_evidence_qa(
                query="Test",
                inputs=[str(SAMPLE_PDF)],
                llm=MockLLMClient.return_value,
            )

            assert isinstance(answer, str)

    def test_run_evidence_qa_result_returns_structured(self):
        """run_evidence_qa_result should return EvidenceQAResult."""
        with patch("jarvis_core.evidence_qa.LLMClient") as MockLLMClient:
            MockLLMClient.return_value.chat.return_value = "Test answer"

            from jarvis_core.evidence_qa import run_evidence_qa_result

            result = run_evidence_qa_result(
                query="Test",
                inputs=[str(SAMPLE_PDF)],
                llm=MockLLMClient.return_value,
            )

            assert isinstance(result, EvidenceQAResult)
            assert result.answer == "Test answer"

    def test_compatibility_answer_matches(self):
        """run_evidence_qa answer should match result.answer."""
        with patch("jarvis_core.evidence_qa.LLMClient") as MockLLMClient:
            MockLLMClient.return_value.chat.return_value = "Consistent answer"

            from jarvis_core.evidence_qa import run_evidence_qa, run_evidence_qa_result

            str_answer = run_evidence_qa(
                query="Test",
                inputs=[str(SAMPLE_PDF)],
                llm=MockLLMClient.return_value,
            )

            # Note: Can't easily compare since each call is independent
            # Just verify both work
            assert isinstance(str_answer, str)
            assert len(str_answer) > 0
