"""Tests for jarvis_core.writing module.

Tests for draft_generator.py and outline_builder.py to improve coverage.
"""

import tempfile
from pathlib import Path


class TestClaimDatum:
    """Tests for ClaimDatum dataclass."""

    def test_create_claim_datum(self):
        from jarvis_core.writing.outline_builder import ClaimDatum

        claim = ClaimDatum(text="Test claim", evidence=[], weak=False, score=0.8)
        assert claim.text == "Test claim"
        assert claim.evidence == []
        assert claim.weak is False
        assert claim.score == 0.8

    def test_claim_datum_with_score_none(self):
        from jarvis_core.writing.outline_builder import ClaimDatum

        claim = ClaimDatum(text="Test claim", evidence=[])
        assert claim.score is None


class TestSection:
    """Tests for Section dataclass."""

    def test_create_section(self):
        from jarvis_core.writing.outline_builder import Section

        section = Section(title="Background", paragraphs=["Para 1", "Para 2"])
        assert section.title == "Background"
        assert len(section.paragraphs) == 2


class TestSortedClaims:
    """Tests for _sorted_claims function."""

    def test_sorted_claims_with_scores(self):
        from jarvis_core.writing.outline_builder import ClaimDatum, _sorted_claims

        claims = [
            ClaimDatum(text="Low", evidence=[], score=0.3),
            ClaimDatum(text="High", evidence=[], score=0.9),
            ClaimDatum(text="Mid", evidence=[], score=0.5),
        ]
        sorted_claims = _sorted_claims(claims)
        assert sorted_claims[0].text == "High"
        assert sorted_claims[2].text == "Low"

    def test_sorted_claims_no_scores(self):
        from jarvis_core.writing.outline_builder import ClaimDatum, _sorted_claims

        claims = [
            ClaimDatum(text="A", evidence=[]),
            ClaimDatum(text="B", evidence=[]),
        ]
        sorted_claims = _sorted_claims(claims)
        assert len(sorted_claims) == 2


class TestBuildResearchPlanSections:
    """Tests for build_research_plan_sections function."""

    def test_build_with_claims(self):
        from jarvis_core.writing.outline_builder import (
            ClaimDatum,
            build_research_plan_sections,
        )

        claims = [
            ClaimDatum(text="Claim 1", evidence=[], score=0.9),
            ClaimDatum(text="Claim 2", evidence=[], score=0.8),
            ClaimDatum(text="Claim 3", evidence=[], score=0.7),
        ]
        sections = build_research_plan_sections(claims, "Overview text", ["Ref1", "Ref2"])
        assert len(sections) == 9  # 9 sections in research plan
        assert sections[0].title == "背景 (Background)"
        assert sections[-1].title == "参考文献 (References)"

    def test_build_with_no_claims(self):
        from jarvis_core.writing.outline_builder import build_research_plan_sections

        sections = build_research_plan_sections([], "", [])
        assert len(sections) == 9
        # Should have fallback paragraphs


class TestBuildThesisOutlineSections:
    """Tests for build_thesis_outline_sections function."""

    def test_build_thesis_outline(self):
        from jarvis_core.writing.outline_builder import (
            ClaimDatum,
            build_thesis_outline_sections,
        )

        claims = [
            ClaimDatum(text="Result 1", evidence=[], score=0.9),
            ClaimDatum(text="Result 2", evidence=[], score=0.8),
        ]
        sections = build_thesis_outline_sections(claims, ["Ref1"])
        assert len(sections) == 8  # 8 sections in thesis outline
        assert sections[0].title == "要旨 (Abstract)"


class TestBuildThesisDraftSections:
    """Tests for build_thesis_draft_sections function."""

    def test_build_thesis_draft(self):
        from jarvis_core.writing.outline_builder import (
            ClaimDatum,
            build_thesis_draft_sections,
        )

        claims = [
            ClaimDatum(text="Result 1", evidence=[], score=0.9),
        ]
        sections = build_thesis_draft_sections(claims, ["Ref1"])
        assert len(sections) >= 1


class TestDraftGeneratorHelpers:
    """Tests for draft_generator.py helper functions."""

    def test_now_returns_iso_format(self):
        from jarvis_core.writing.draft_generator import _now

        result = _now()
        assert "T" in result  # ISO format has T separator

    def test_safe_read_json_nonexistent(self):
        from jarvis_core.writing.draft_generator import _safe_read_json

        result = _safe_read_json(Path("/nonexistent/path.json"))
        assert result == {}

    def test_normalize_evidence(self):
        from jarvis_core.writing.draft_generator import _normalize_evidence

        item = {"paper_id": "p1", "chunk_id": "c1", "section": "intro"}
        locator = _normalize_evidence(item)
        assert locator.paper_id == "p1"
        assert locator.chunk_id == "c1"

    def test_extract_evidence_empty(self):
        from jarvis_core.writing.draft_generator import _extract_evidence

        result = _extract_evidence(None)
        assert result == []

    def test_extract_evidence_list(self):
        from jarvis_core.writing.draft_generator import _extract_evidence

        raw = [{"paper_id": "p1", "chunk_id": "c1"}]
        result = _extract_evidence(raw)
        assert len(result) == 1
        assert result[0].paper_id == "p1"


class TestSectionsToMarkdown:
    """Tests for _sections_to_markdown function."""

    def test_sections_to_markdown(self):
        from jarvis_core.writing.draft_generator import _sections_to_markdown
        from jarvis_core.writing.outline_builder import Section

        sections = [
            Section(title="Title 1", paragraphs=["Para 1", "Para 2"]),
            Section(title="Title 2", paragraphs=["- Item 1", "- Item 2"]),
        ]
        md = _sections_to_markdown(sections)
        assert "## Title 1" in md
        assert "## Title 2" in md
        assert "Para 1" in md


class TestLoadClaims:
    """Tests for load_claims function."""

    def test_load_claims_no_dir(self):
        from jarvis_core.writing.draft_generator import load_claims

        with tempfile.TemporaryDirectory() as tmpdir:
            claims = load_claims(Path(tmpdir))
            assert claims == []

    def test_load_claims_with_data(self):
        import json

        from jarvis_core.writing.draft_generator import load_claims

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            claims_dir = run_dir / "claims"
            claims_dir.mkdir()

            data = [
                {
                    "claim": "Test claim 1",
                    "score": 0.9,
                    "evidence": [{"paper_id": "p1", "chunk_id": "c1"}],
                },
                {"text": "Test claim 2", "weak": True},
                {"statement": "Test claim 3", "rank_score": 0.7},
            ]
            with open(claims_dir / "test.claims.jsonl", "w", encoding="utf-8") as f:
                for item in data:
                    f.write(json.dumps(item) + "\n")

            claims = load_claims(run_dir)
            assert len(claims) == 3
            assert claims[0].text == "Test claim 1"
            assert claims[0].score == 0.9
            assert len(claims[0].evidence) == 1
            assert claims[1].weak is True


class TestCitationFormatter:
    """Tests for citation_formatter.py."""

    def test_evidence_locator_creation(self):
        from jarvis_core.writing.citation_formatter import EvidenceLocator

        locator = EvidenceLocator(
            paper_id="p1",
            chunk_id="c1",
            section="intro",
            paragraph="p1",
            sentence="s1",
            weak=True,
        )
        assert locator.paper_id == "p1"
        assert locator.weak is True

    def test_format_evidence_locator_empty(self):
        from jarvis_core.writing.citation_formatter import format_evidence_locator

        result = format_evidence_locator([])
        assert "unknown" in result

    def test_format_evidence_locator_with_items(self):
        from jarvis_core.writing.citation_formatter import EvidenceLocator, format_evidence_locator

        items = [
            EvidenceLocator("p1", "c1", "intro", "para1", "sent1", False),
            EvidenceLocator("p2", "c2", "methods", "para2", "sent2", False),
        ]
        result = format_evidence_locator(items)
        assert "p1" in result
        assert "p2" in result

    def test_has_weak_evidence_true(self):
        from jarvis_core.writing.citation_formatter import EvidenceLocator, has_weak_evidence

        items = [
            EvidenceLocator("p1", "c1", "intro", "para1", "sent1", False),
            EvidenceLocator("p2", "c2", "methods", "para2", "sent2", True),
        ]
        assert has_weak_evidence(items) is True

    def test_has_weak_evidence_false(self):
        from jarvis_core.writing.citation_formatter import EvidenceLocator, has_weak_evidence

        items = [
            EvidenceLocator("p1", "c1", "intro", "para1", "sent1", False),
        ]
        assert has_weak_evidence(items) is False


class TestUtils:
    """Tests for utils.py."""

    def test_load_overview_exists(self):
        from jarvis_core.writing.utils import load_overview

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            notes_dir = run_dir / "notes"
            notes_dir.mkdir()
            overview_path = notes_dir / "00_RUN_OVERVIEW.md"
            overview_path.write_text("Test overview content", encoding="utf-8")

            result = load_overview(run_dir)
            assert result == "Test overview content"

    def test_load_overview_missing(self):
        from jarvis_core.writing.utils import load_overview

        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_overview(Path(tmpdir))
            assert result == ""


class TestExtractEvidenceAdditional:
    """Additional tests for _extract_evidence function."""

    def test_extract_evidence_dict(self):
        from jarvis_core.writing.draft_generator import _extract_evidence

        raw = {"paper_id": "p1", "chunk_id": "c1"}
        result = _extract_evidence(raw)
        assert len(result) == 1
        assert result[0].paper_id == "p1"

    def test_extract_evidence_string(self):
        from jarvis_core.writing.draft_generator import _extract_evidence

        raw = "some_string"
        result = _extract_evidence(raw)
        assert len(result) == 1
        assert result[0].chunk_id == "some_string"

    def test_extract_evidence_list_with_strings(self):
        from jarvis_core.writing.draft_generator import _extract_evidence

        raw = ["chunk1", "chunk2"]
        result = _extract_evidence(raw)
        assert len(result) == 2
        assert result[0].chunk_id == "chunk1"


class TestLoadReferences:
    """Tests for _load_references function."""

    def test_load_references_from_file(self):
        import json

        from jarvis_core.writing.draft_generator import _load_references

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            data = {"papers": [{"paper_id": "p1", "title": "Test Paper"}]}
            rank_path = run_dir / "research_rank.json"
            rank_path.write_text(json.dumps(data), encoding="utf-8")

            refs = _load_references(run_dir, [])
            assert len(refs) == 1
            assert "p1" in refs[0]

    def test_load_references_from_claims(self):
        from jarvis_core.writing.citation_formatter import EvidenceLocator
        from jarvis_core.writing.draft_generator import _load_references
        from jarvis_core.writing.outline_builder import ClaimDatum

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            claims = [
                ClaimDatum(
                    text="Test",
                    evidence=[EvidenceLocator("p1", "c1", "intro", "p1", "s1", False)],
                ),
            ]
            refs = _load_references(run_dir, claims)
            assert "p1" in refs


class TestGenerateMarkdown:
    """Tests for generate_markdown_* functions."""

    def test_generate_markdown_research_plan(self):
        from jarvis_core.writing.draft_generator import generate_markdown_research_plan
        from jarvis_core.writing.outline_builder import ClaimDatum

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            claims = [ClaimDatum(text="Test claim", evidence=[], score=0.9)]
            result = generate_markdown_research_plan(run_dir, claims)
            assert "# Research Plan Draft" in result
            assert "背景" in result

    def test_generate_markdown_thesis_outline(self):
        from jarvis_core.writing.draft_generator import generate_markdown_thesis_outline
        from jarvis_core.writing.outline_builder import ClaimDatum

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            claims = [ClaimDatum(text="Test claim", evidence=[])]
            result = generate_markdown_thesis_outline(run_dir, claims)
            assert "# Thesis Outline" in result

    def test_generate_markdown_thesis_draft(self):
        from jarvis_core.writing.draft_generator import generate_markdown_thesis_draft
        from jarvis_core.writing.outline_builder import ClaimDatum

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            claims = [ClaimDatum(text="Test claim", evidence=[])]
            result = generate_markdown_thesis_draft(run_dir, claims)
            assert "# Thesis Draft" in result


class TestWriteHelpers:
    """Tests for _write_text, _write_readme, _update_manifest functions."""

    def test_write_text(self):
        from jarvis_core.writing.draft_generator import _write_text

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "test.txt"
            _write_text(path, "Hello World")
            assert path.exists()
            assert path.read_text(encoding="utf-8") == "Hello World"

    def test_write_readme(self):
        from jarvis_core.writing.draft_generator import _write_readme

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            _write_readme(run_dir)
            readme_path = run_dir / "writing" / "README.md"
            assert readme_path.exists()
            content = readme_path.read_text(encoding="utf-8")
            assert "Writing Outputs" in content

    def test_update_manifest_no_manifest(self):

        from jarvis_core.writing.draft_generator import _update_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            # Should not raise even without manifest file
            _update_manifest(run_dir, ["test.md"])
            # No manifest should be created
            assert not (run_dir / "manifest.json").exists()

    def test_update_manifest_with_manifest(self):
        import json

        from jarvis_core.writing.draft_generator import _update_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            manifest_path = run_dir / "manifest.json"
            manifest_path.write_text('{"existing": "data"}', encoding="utf-8")

            _update_manifest(run_dir, ["test.md", "test2.md"])

            updated = json.loads(manifest_path.read_text(encoding="utf-8"))
            assert updated["existing"] == "data"
            assert "writing_template_version" in updated
            assert "writing_outputs" in updated
            assert len(updated["writing_outputs"]) == 2


class TestBuildMetadataHeader:
    """Tests for _build_metadata_header function."""

    def test_build_metadata_header(self):
        from jarvis_core.writing.draft_generator import _build_metadata_header

        result = _build_metadata_header("test_run_id")
        assert "test_run_id" in result
        assert "template_version" in result
        assert "generated_at" in result
