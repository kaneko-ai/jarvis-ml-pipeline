"""Tests for Bibliography Export (RP15).

Per RP15, these tests verify:
- BibTeX export
- RIS export (Zotero/EndNote compatible)
- Bundle includes .bib/.ris files
"""

from jarvis_core.bibtex_utils import _escape_bibtex, export_bibtex, format_bibtex_entry
from jarvis_core.reference import Reference
from jarvis_core.ris import export_ris, format_ris_entry
import tempfile
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


class TestBibTeX:
    """Tests for BibTeX export."""

    def test_escape_special_chars(self):
        """Should escape LaTeX special characters."""
        assert _escape_bibtex("test & test") == r"test \& test"
        assert _escape_bibtex("100%") == r"100\%"

    def test_format_single_entry(self):
        """Should format a single BibTeX entry."""
        ref = Reference(
            id="R1",
            source_type="pdf",
            locator="pdf:paper.pdf",
            title="Test Paper",
            year=2023,
            pages=[1, 2, 3],
        )
        entry = format_bibtex_entry(ref)

        assert "@misc{" in entry
        assert "title" in entry
        assert "2023" in entry

    def test_format_url_reference(self):
        """Should include URL for web sources."""
        ref = Reference(
            id="R1",
            source_type="url",
            locator="url:https://example.com",
            title="Web Article",
        )
        entry = format_bibtex_entry(ref)

        assert "url" in entry.lower()
        assert "example.com" in entry

    def test_export_multiple(self):
        """Should export multiple references."""
        refs = [
            Reference(id="R1", source_type="pdf", locator="pdf:a.pdf"),
            Reference(id="R2", source_type="url", locator="url:https://b.com"),
        ]
        output = export_bibtex(refs)

        assert output.count("@misc{") == 2

    def test_export_empty_list(self):
        """Should handle empty list."""
        output = export_bibtex([])
        assert "No references" in output


class TestRIS:
    """Tests for RIS export."""

    def test_format_single_entry(self):
        """Should format a single RIS entry."""
        ref = Reference(
            id="R1",
            source_type="pdf",
            locator="pdf:paper.pdf",
            title="Test Paper",
            year=2023,
        )
        entry = format_ris_entry(ref)

        assert "TY  - GEN" in entry  # Type
        assert "TI  - Test Paper" in entry  # Title
        assert "PY  - 2023" in entry  # Year
        assert "ER  - " in entry  # End of record

    def test_format_with_authors(self):
        """Should include authors."""
        ref = Reference(
            id="R1",
            source_type="pdf",
            locator="pdf:x",
            authors=["Smith, J.", "Doe, A."],
        )
        entry = format_ris_entry(ref)

        assert "AU  - Smith, J." in entry
        assert "AU  - Doe, A." in entry

    def test_format_url(self):
        """Should include URL for web sources."""
        ref = Reference(
            id="R1",
            source_type="url",
            locator="url:https://example.com",
        )
        entry = format_ris_entry(ref)

        assert "UR  - https://example.com" in entry

    def test_export_multiple(self):
        """Should export multiple references."""
        refs = [
            Reference(id="R1", source_type="pdf", locator="pdf:a.pdf"),
            Reference(id="R2", source_type="url", locator="url:https://b.com"),
        ]
        output = export_ris(refs)

        # Each entry has TY and ER
        assert output.count("TY  - GEN") == 2
        assert output.count("ER  - ") == 2


class TestBundleBibliography:
    """Tests for bundle .bib/.ris generation."""

    def test_bundle_includes_bib(self):
        """Bundle should include references.bib."""
        from jarvis_core.agents import Citation
        from jarvis_core.bundle import export_evidence_bundle
        from jarvis_core.evidence import EvidenceStore
        from jarvis_core.result import EvidenceQAResult

        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "pdf:test.pdf#page:1", "Content")

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[
                Citation(chunk_id=chunk_id, source="pdf", locator="pdf:test.pdf#page:1", quote=""),
            ],
            inputs=[],
            query="Query",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            bib_path = Path(tmpdir) / "references.bib"
            assert bib_path.exists()

            content = bib_path.read_text(encoding="utf-8")
            assert "@misc{" in content

    def test_bundle_includes_ris(self):
        """Bundle should include references.ris."""
        from jarvis_core.agents import Citation
        from jarvis_core.bundle import export_evidence_bundle
        from jarvis_core.evidence import EvidenceStore
        from jarvis_core.result import EvidenceQAResult

        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "pdf:test.pdf#page:1", "Content")

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[
                Citation(chunk_id=chunk_id, source="pdf", locator="pdf:test.pdf#page:1", quote=""),
            ],
            inputs=[],
            query="Query",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            ris_path = Path(tmpdir) / "references.ris"
            assert ris_path.exists()

            content = ris_path.read_text(encoding="utf-8")
            assert "TY  - GEN" in content