"""Tests for Knowledge Tool Integration (RP19).

Per RP19, these tests verify:
- NotebookLM export
- Obsidian vault export (with wikilinks)
- Notion JSON export
- Bundle includes all integration files
"""
import json
import sys
import tempfile
from pathlib import Path

import pytest

# PR-59: Mark all tests in this file as core
pytestmark = pytest.mark.core

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.claim import ClaimSet
from jarvis_core.integrations.notebooklm import export_notebooklm
from jarvis_core.integrations.notion import export_notion
from jarvis_core.integrations.obsidian import _safe_filename, export_obsidian
from jarvis_core.reference import Reference


class TestNotebookLM:
    """Tests for NotebookLM export."""

    def test_export_contains_query(self):
        """Should include query in output."""
        from jarvis_core.result import EvidenceQAResult

        result = EvidenceQAResult(
            answer="Test answer",
            status="success",
            citations=[],
            inputs=[],
            query="What is CD73?",
        )

        output = export_notebooklm(result, [])

        assert "What is CD73?" in output

    def test_export_contains_answer(self):
        """Should include answer."""
        from jarvis_core.result import EvidenceQAResult

        result = EvidenceQAResult(
            answer="CD73 is an ectoenzyme.",
            status="success",
            citations=[],
            inputs=[],
            query="Query",
        )

        output = export_notebooklm(result, [])

        assert "CD73 is an ectoenzyme" in output

    def test_export_contains_claims(self):
        """Should include claims if present."""
        from jarvis_core.result import EvidenceQAResult

        cs = ClaimSet()
        cs.add_new("First claim.", [])

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[],
            inputs=[],
            query="Query",
            claims=cs,
        )

        output = export_notebooklm(result, [])

        assert "First claim" in output
        assert "Key Findings" in output


class TestObsidian:
    """Tests for Obsidian export."""

    def test_safe_filename(self):
        """Should sanitize filenames."""
        assert _safe_filename("What is CD73?") == "What is CD73_"
        assert _safe_filename("test/path:name") == "test_path_name"

    def test_export_creates_structure(self):
        """Should create vault structure."""
        from jarvis_core.agents import Citation
        from jarvis_core.result import EvidenceQAResult

        cs = ClaimSet()
        cs.add_new("Test claim.", ["chunk_abc"])

        refs = [Reference(
            id="R1",
            source_type="pdf",
            locator="pdf:paper.pdf",
            chunk_ids=["chunk_abc"],
        )]

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[Citation(chunk_id="chunk_abc", source="pdf", locator="pdf:x", quote="")],
            inputs=[],
            query="Test query",
            claims=cs,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "obsidian"
            export_obsidian(result, refs, str(out_dir))

            # Check structure
            assert out_dir.exists()
            assert (out_dir / "notes").exists()
            assert (out_dir / "sources").exists()
            assert (out_dir / "index.md").exists()

    def test_export_creates_wikilinks(self):
        """Should use wikilinks in notes."""
        from jarvis_core.agents import Citation
        from jarvis_core.result import EvidenceQAResult

        cs = ClaimSet()
        cs.add_new("Test claim.", ["chunk_abc"])

        refs = [Reference(
            id="R1",
            source_type="pdf",
            locator="pdf:paper.pdf",
            chunk_ids=["chunk_abc"],
        )]

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[Citation(chunk_id="chunk_abc", source="pdf", locator="pdf:x", quote="")],
            inputs=[],
            query="Test",
            claims=cs,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "obsidian"
            export_obsidian(result, refs, str(out_dir))

            # Check for wikilinks in claim note
            claim_files = list((out_dir / "notes").glob("Claim_*.md"))
            assert len(claim_files) > 0

            content = claim_files[0].read_text(encoding="utf-8")
            assert "[[" in content  # Contains wikilinks


class TestNotion:
    """Tests for Notion export."""

    def test_export_valid_json(self):
        """Should export valid JSON."""
        from jarvis_core.result import EvidenceQAResult

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[],
            inputs=[],
            query="Query",
        )

        output = export_notion(result, [])
        data = json.loads(output)

        assert data["query"] == "Query"
        assert data["answer"] == "Answer"

    def test_export_includes_claims(self):
        """Should include claims in export."""
        from jarvis_core.result import EvidenceQAResult

        cs = ClaimSet()
        cs.add_new("Test claim.", [])

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[],
            inputs=[],
            query="Query",
            claims=cs,
        )

        output = export_notion(result, [])
        data = json.loads(output)

        assert len(data["claims"]) == 1
        assert data["claims"][0]["text"] == "Test claim."


class TestBundleIntegrations:
    """Tests for bundle integration exports."""

    def test_bundle_includes_notebooklm(self):
        """Bundle should include notebooklm.md."""
        from jarvis_core.agents import Citation
        from jarvis_core.bundle import export_evidence_bundle
        from jarvis_core.evidence import EvidenceStore
        from jarvis_core.result import EvidenceQAResult

        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "pdf:test.pdf", "Content")

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[Citation(chunk_id=chunk_id, source="pdf", locator="pdf:x", quote="")],
            inputs=[],
            query="Query",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            assert (Path(tmpdir) / "notebooklm.md").exists()

    def test_bundle_includes_obsidian(self):
        """Bundle should include obsidian directory."""
        from jarvis_core.agents import Citation
        from jarvis_core.bundle import export_evidence_bundle
        from jarvis_core.evidence import EvidenceStore
        from jarvis_core.result import EvidenceQAResult

        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "pdf:test.pdf", "Content")

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[Citation(chunk_id=chunk_id, source="pdf", locator="pdf:x", quote="")],
            inputs=[],
            query="Query",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            assert (Path(tmpdir) / "obsidian").exists()
            assert (Path(tmpdir) / "obsidian" / "index.md").exists()

    def test_bundle_includes_notion(self):
        """Bundle should include notion.json."""
        from jarvis_core.agents import Citation
        from jarvis_core.bundle import export_evidence_bundle
        from jarvis_core.evidence import EvidenceStore
        from jarvis_core.result import EvidenceQAResult

        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "pdf:test.pdf", "Content")

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[Citation(chunk_id=chunk_id, source="pdf", locator="pdf:x", quote="")],
            inputs=[],
            query="Query",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            notion_path = Path(tmpdir) / "notion.json"
            assert notion_path.exists()

            with open(notion_path) as f:
                data = json.load(f)
            assert data["type"] == "jarvis_evidence_export"
