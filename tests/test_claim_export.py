"""Tests for Claim Reuse & Structure Export (RP16).

Per RP16, these tests verify:
- Claim export to Markdown/JSON/PPTX outline
- Bundle includes claims.md, claims.json, slides_outline.txt
"""
import json
import tempfile
from pathlib import Path
import sys

import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.claim import Claim, ClaimSet
from jarvis_core.reference import Reference
from jarvis_core.claim_export import (
    export_claims,
    export_claims_markdown,
    export_claims_json,
    export_claims_pptx_outline,
)


class TestClaimExportMarkdown:
    """Tests for Markdown export."""

    def test_export_single_claim(self):
        """Should export single claim to Markdown."""
        cs = ClaimSet()
        cs.add_new("CD73 is an ectoenzyme.", ["chunk_abc"])

        output = export_claims_markdown(cs)

        assert "Claim 1" in output
        assert "CD73 is an ectoenzyme" in output

    def test_export_multiple_claims(self):
        """Should export multiple claims."""
        cs = ClaimSet()
        cs.add_new("First claim.", ["c1"])
        cs.add_new("Second claim.", ["c2"])

        output = export_claims_markdown(cs)

        assert "Claim 1" in output
        assert "Claim 2" in output

    def test_includes_sources(self):
        """Should include source information."""
        cs = ClaimSet()
        cs.add_new("Test claim.", ["chunk_123"])

        output = export_claims_markdown(cs)

        assert "Sources" in output


class TestClaimExportJSON:
    """Tests for JSON export."""

    def test_export_valid_json(self):
        """Should export valid JSON."""
        cs = ClaimSet()
        cs.add_new("Test claim.", ["c1"])

        output = export_claims_json(cs)
        data = json.loads(output)

        assert "claims" in data
        assert len(data["claims"]) == 1

    def test_includes_references(self):
        """Should map citations to references."""
        cs = ClaimSet()
        cs.add_new("Test.", ["chunk_abc"])

        refs = [Reference(
            id="R1",
            source_type="pdf",
            locator="pdf:test.pdf",
            chunk_ids=["chunk_abc"],
        )]

        output = export_claims_json(cs, refs)
        data = json.loads(output)

        assert data["claims"][0]["references"] == ["R1"]


class TestClaimExportPPTX:
    """Tests for PPTX outline export."""

    def test_export_outline(self):
        """Should generate slide outline."""
        cs = ClaimSet()
        cs.add_new("First claim about CD73.", ["c1"])
        cs.add_new("Second claim about TME.", ["c2"])

        output = export_claims_pptx_outline(cs, title="CD73 Research")

        assert "PRESENTATION OUTLINE" in output
        assert "CD73 Research" in output
        assert "Slide 1" in output
        assert "Slide 2" in output

    def test_skips_invalid_claims(self):
        """Should skip invalid claims in presentation."""
        cs = ClaimSet()
        c1 = cs.add_new("Valid claim.", ["c1"])
        c2 = cs.add_new("Invalid claim.", [])
        c2.valid = False

        output = export_claims_pptx_outline(cs)

        assert "Valid claim" in output
        assert "Invalid claim" not in output


class TestExportClaimsFunction:
    """Tests for the main export_claims function."""

    def test_format_markdown(self):
        """Should export as Markdown."""
        cs = ClaimSet()
        cs.add_new("Test.", [])

        output = export_claims(cs, format="markdown")
        assert "# Claims" in output

    def test_format_json(self):
        """Should export as JSON."""
        cs = ClaimSet()
        cs.add_new("Test.", [])

        output = export_claims(cs, format="json")
        data = json.loads(output)
        assert "claims" in data

    def test_format_pptx_outline(self):
        """Should export as PPTX outline."""
        cs = ClaimSet()
        cs.add_new("Test.", [])

        output = export_claims(cs, format="pptx_outline")
        assert "PRESENTATION OUTLINE" in output


class TestBundleClaimsExport:
    """Tests for bundle claims export."""

    def test_bundle_includes_claims_md(self):
        """Bundle should include claims.md."""
        from jarvis_core.agents import Citation
        from jarvis_core.evidence import EvidenceStore
        from jarvis_core.result import EvidenceQAResult
        from jarvis_core.bundle import export_evidence_bundle

        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "pdf:test.pdf#page:1", "Content")

        # Create result with claims
        cs = ClaimSet()
        cs.add_new("Test claim.", [chunk_id])

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[
                Citation(chunk_id=chunk_id, source="pdf", locator="pdf:test.pdf", quote=""),
            ],
            inputs=[],
            query="Query",
            claims=cs,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            claims_md = Path(tmpdir) / "claims.md"
            assert claims_md.exists()

    def test_bundle_includes_claims_json(self):
        """Bundle should include claims.json."""
        from jarvis_core.agents import Citation
        from jarvis_core.evidence import EvidenceStore
        from jarvis_core.result import EvidenceQAResult
        from jarvis_core.bundle import export_evidence_bundle

        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "pdf:test.pdf", "Content")

        cs = ClaimSet()
        cs.add_new("Test.", [chunk_id])

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[Citation(chunk_id=chunk_id, source="pdf", locator="pdf:x", quote="")],
            inputs=[],
            query="Query",
            claims=cs,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            claims_json = Path(tmpdir) / "claims.json"
            assert claims_json.exists()

            with open(claims_json) as f:
                data = json.load(f)
            assert "claims" in data

    def test_bundle_includes_slides_outline(self):
        """Bundle should include slides_outline.txt."""
        from jarvis_core.agents import Citation
        from jarvis_core.evidence import EvidenceStore
        from jarvis_core.result import EvidenceQAResult
        from jarvis_core.bundle import export_evidence_bundle

        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "pdf:test.pdf", "Content")

        cs = ClaimSet()
        cs.add_new("Test.", [chunk_id])

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[Citation(chunk_id=chunk_id, source="pdf", locator="pdf:x", quote="")],
            inputs=[],
            query="My Research Question",
            claims=cs,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            slides = Path(tmpdir) / "slides_outline.txt"
            assert slides.exists()

            content = slides.read_text(encoding="utf-8")
            assert "My Research Question" in content
