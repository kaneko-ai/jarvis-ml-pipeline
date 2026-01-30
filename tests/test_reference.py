"""Tests for Reference List Generator (RP14).

Per RP14, these tests verify:
- Reference structure
- Chunk to Reference normalization
- Vancouver/APA formatting
- Bundle references.md generation
"""

from jarvis_core.agents import Citation
from jarvis_core.reference import Reference, _parse_locator, extract_references
from jarvis_core.reference_formatter import (
    format_apa,
    format_references,
    format_vancouver,
)
import tempfile
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


class TestReference:
    """Tests for Reference dataclass."""

    def test_create_reference(self):
        """Should create reference."""
        ref = Reference(
            id="R1",
            source_type="pdf",
            locator="pdf:paper.pdf",
            title="Test Paper",
            pages=[1, 2, 3],
        )
        assert ref.id == "R1"
        assert ref.source_type == "pdf"
        assert ref.pages == [1, 2, 3]

    def test_get_pages_display_single(self):
        """Should format single page."""
        ref = Reference(id="R1", source_type="pdf", locator="pdf:x", pages=[5])
        assert ref.get_pages_display() == "p. 5"

    def test_get_pages_display_range(self):
        """Should format page range."""
        ref = Reference(id="R1", source_type="pdf", locator="pdf:x", pages=[1, 2, 3])
        assert ref.get_pages_display() == "pp. 1-3"

    def test_get_pages_display_mixed(self):
        """Should format mixed pages."""
        ref = Reference(id="R1", source_type="pdf", locator="pdf:x", pages=[1, 2, 5, 6, 7, 10])
        display = ref.get_pages_display()
        assert "1-2" in display
        assert "5-7" in display
        assert "10" in display

    def test_to_dict_from_dict(self):
        """Should serialize and deserialize."""
        ref = Reference(
            id="R1",
            source_type="url",
            locator="url:https://example.com",
            title="Example",
            year=2023,
        )
        d = ref.to_dict()
        ref2 = Reference.from_dict(d)

        assert ref2.id == "R1"
        assert ref2.title == "Example"
        assert ref2.year == 2023


class TestParseLocator:
    """Tests for locator parsing."""

    def test_parse_pdf_locator(self):
        """Should parse PDF locator."""
        base, source_type, page = _parse_locator("pdf:paper.pdf#page:3#chunk:0")
        assert source_type == "pdf"
        assert page == 3
        assert "paper.pdf" in base

    def test_parse_url_locator(self):
        """Should parse URL locator."""
        base, source_type, page = _parse_locator("url:https://example.com#chunk:0")
        assert source_type == "url"
        assert page is None


class TestExtractReferences:
    """Tests for reference extraction."""

    def test_multiple_chunks_same_pdf(self):
        """Multiple chunks from same PDF should become one reference."""
        citations = [
            Citation(chunk_id="c1", source="pdf", locator="pdf:paper.pdf#page:1#chunk:0", quote=""),
            Citation(chunk_id="c2", source="pdf", locator="pdf:paper.pdf#page:2#chunk:0", quote=""),
            Citation(chunk_id="c3", source="pdf", locator="pdf:paper.pdf#page:3#chunk:0", quote=""),
        ]

        refs = extract_references(citations)

        assert len(refs) == 1
        assert refs[0].pages == [1, 2, 3]
        assert refs[0].chunk_ids == ["c1", "c2", "c3"]

    def test_mixed_pdf_url(self):
        """PDF and URL should become separate references."""
        citations = [
            Citation(chunk_id="c1", source="pdf", locator="pdf:paper.pdf#page:1", quote=""),
            Citation(chunk_id="c2", source="url", locator="url:https://example.com", quote=""),
        ]

        refs = extract_references(citations)

        assert len(refs) == 2


class TestFormatter:
    """Tests for reference formatters."""

    def test_format_vancouver(self):
        """Should format in Vancouver style."""
        ref = Reference(
            id="R1",
            source_type="pdf",
            locator="pdf:paper.pdf",
            title="Test Paper",
            year=2023,
            pages=[1, 2],
        )
        formatted = format_vancouver(ref, 1)

        assert "[1]" in formatted
        assert "Test Paper" in formatted
        assert "2023" in formatted

    def test_format_apa(self):
        """Should format in APA style."""
        ref = Reference(
            id="R1",
            source_type="url",
            locator="url:https://example.com",
            title="Example Article",
            authors=["Smith, J.", "Doe, A."],
            year=2022,
        )
        formatted = format_apa(ref, 1)

        assert "Smith" in formatted
        assert "(2022)" in formatted
        assert "Example Article" in formatted

    def test_format_references_list(self):
        """Should format multiple references."""
        refs = [
            Reference(id="R1", source_type="pdf", locator="pdf:a.pdf"),
            Reference(id="R2", source_type="url", locator="url:https://b.com"),
        ]

        output = format_references(refs, style="vancouver")
        lines = output.split("\n")

        assert len(lines) == 2
        assert "[1]" in lines[0]
        assert "[2]" in lines[1]


class TestBundleReferences:
    """Tests for bundle references.md generation."""

    def test_bundle_includes_references_md(self):
        """Bundle should include references.md."""
        from jarvis_core.bundle import export_evidence_bundle
        from jarvis_core.evidence import EvidenceStore
        from jarvis_core.result import EvidenceQAResult

        store = EvidenceStore()
        chunk_id = store.add_chunk(
            "pdf",
            "pdf:paper.pdf#page:1#chunk:0",
            "Test content",
        )

        result = EvidenceQAResult(
            answer="Test",
            status="success",
            citations=[
                Citation(
                    chunk_id=chunk_id, source="pdf", locator="pdf:paper.pdf#page:1", quote="q"
                ),
            ],
            inputs=["paper.pdf"],
            query="Test query",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            refs_path = Path(tmpdir) / "references.md"
            assert refs_path.exists()

            content = refs_path.read_text(encoding="utf-8")
            assert "References" in content

    def test_bundle_json_includes_references(self):
        """bundle.json should include references."""
        import json

        from jarvis_core.bundle import export_evidence_bundle
        from jarvis_core.evidence import EvidenceStore
        from jarvis_core.result import EvidenceQAResult

        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "pdf:test.pdf#page:5", "Content")

        result = EvidenceQAResult(
            answer="Answer",
            status="success",
            citations=[
                Citation(chunk_id=chunk_id, source="pdf", locator="pdf:test.pdf#page:5", quote=""),
            ],
            inputs=[],
            query="Query",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_evidence_bundle(result, store, tmpdir)

            bundle_path = Path(tmpdir) / "bundle.json"
            with open(bundle_path) as f:
                data = json.load(f)

            assert "references" in data
            assert len(data["references"]) == 1
