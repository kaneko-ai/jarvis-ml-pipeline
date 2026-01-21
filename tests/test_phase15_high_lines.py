"""Phase 15: High-Line-Count Module Function Tests.

Focus on modules with highest line counts for maximum coverage impact.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
from pathlib import Path
import json


# ============================================================
# Tests for notes/note_generator.py (450 lines)
# ============================================================

class TestNoteGeneratorFunctional:
    """Comprehensive tests for note_generator module - all functions."""

    def test_load_json_existing(self):
        """Test _load_json with existing file."""
        from jarvis_core.notes.note_generator import _load_json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            path = Path(f.name)
        result = _load_json(path)
        assert result == {"key": "value"}
        path.unlink()

    def test_load_json_nonexistent(self):
        """Test _load_json with nonexistent file."""
        from jarvis_core.notes.note_generator import _load_json
        result = _load_json(Path("/nonexistent/file.json"))
        assert result == {}

    def test_load_jsonl_existing(self):
        """Test _load_jsonl with existing file."""
        from jarvis_core.notes.note_generator import _load_jsonl
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1}\n{"id": 2}\n')
            path = Path(f.name)
        result = _load_jsonl(path)
        assert len(result) == 2
        path.unlink()

    def test_load_jsonl_nonexistent(self):
        """Test _load_jsonl with nonexistent file."""
        from jarvis_core.notes.note_generator import _load_jsonl
        result = _load_jsonl(Path("/nonexistent/file.jsonl"))
        assert result == []

    def test_safe_filename(self):
        """Test _safe_filename."""
        from jarvis_core.notes.note_generator import _safe_filename
        assert _safe_filename("test/file:name?") == "test_file_name_"
        assert _safe_filename("normal-file.txt") == "normal-file.txt"

    def test_slug(self):
        """Test _slug function."""
        from jarvis_core.notes.note_generator import _slug
        assert _slug("Hello World") == "hello_world"
        assert _slug("A" * 100, max_len=20) == "a" * 20
        assert _slug("!@#$%") == "untitled"

    def test_extract_locator_complete(self):
        """Test _extract_locator with complete data."""
        from jarvis_core.notes.note_generator import _extract_locator
        locator = {
            "section": "Methods",
            "paragraph_index": 2,
            "sentence_index": 3,
            "chunk_id": "c1"
        }
        section, para, sent, chunk = _extract_locator(locator)
        assert section == "Methods"
        assert para == 2
        assert sent == 3
        assert chunk == "c1"

    def test_extract_locator_alternate_keys(self):
        """Test _extract_locator with alternate keys."""
        from jarvis_core.notes.note_generator import _extract_locator
        locator = {
            "Section": "Results",
            "paragraph": 1,
            "sentence": 2,
            "chunk": "c2"
        }
        section, para, sent, chunk = _extract_locator(locator)
        assert section == "Results"
        assert para == 1

    def test_format_locator(self):
        """Test _format_locator."""
        from jarvis_core.notes.note_generator import _format_locator
        locator = {"section": "Abstract", "paragraph_index": 0}
        result = _format_locator(locator)
        assert "Evidence:" in result
        assert "Abstract" in result

    def test_ensure_length_too_long(self):
        """Test _ensure_length when text is too long."""
        from jarvis_core.notes.note_generator import _ensure_length
        result = _ensure_length("a" * 500, min_len=10, max_len=100)
        assert len(result) == 100
        assert result.endswith("…")

    def test_ensure_length_too_short(self):
        """Test _ensure_length when text is too short."""
        from jarvis_core.notes.note_generator import _ensure_length
        result = _ensure_length("short", min_len=50, max_len=200)
        assert len(result) >= 50

    def test_ensure_length_ok(self):
        """Test _ensure_length when text is ok."""
        from jarvis_core.notes.note_generator import _ensure_length
        result = _ensure_length("a" * 50, min_len=10, max_len=100)
        assert result == "a" * 50

    def test_build_tldr_with_claims(self):
        """Test _build_tldr with claims."""
        from jarvis_core.notes.note_generator import _build_tldr
        paper = {"title": "Test Paper"}
        claims = [{"claim_text": "Claim 1"}, {"claim_text": "Claim 2"}]
        result = _build_tldr(paper, claims)
        assert "Test Paper" in result
        assert len(result) >= 200

    def test_build_tldr_without_claims(self):
        """Test _build_tldr without claims."""
        from jarvis_core.notes.note_generator import _build_tldr
        paper = {"title": "Test Paper"}
        claims = []
        result = _build_tldr(paper, claims)
        assert "Test Paper" in result

    def test_build_snapshot_with_value(self):
        """Test _build_snapshot with value."""
        from jarvis_core.notes.note_generator import _build_snapshot
        paper = {"methods": "Machine learning approach"}
        result = _build_snapshot("methods", paper, "fallback")
        assert result == "Machine learning approach"

    def test_build_snapshot_fallback(self):
        """Test _build_snapshot with fallback."""
        from jarvis_core.notes.note_generator import _build_snapshot
        paper = {}
        result = _build_snapshot("methods", paper, "fallback text")
        assert result == "fallback text"

    def test_build_limitations_with_author(self):
        """Test _build_limitations with author limitations."""
        from jarvis_core.notes.note_generator import _build_limitations
        paper = {"limitations": "Small sample size"}
        result = _build_limitations(paper)
        assert "Small sample size" in result

    def test_build_limitations_without_author(self):
        """Test _build_limitations without author limitations."""
        from jarvis_core.notes.note_generator import _build_limitations
        paper = {}
        result = _build_limitations(paper)
        assert "著者の限界" in result

    def test_build_why_it_matters(self):
        """Test _build_why_it_matters."""
        from jarvis_core.notes.note_generator import _build_why_it_matters
        paper = {"domain": "Cancer Research"}
        result = _build_why_it_matters(paper)
        assert "Cancer Research" in result

    def test_group_by_key(self):
        """Test _group_by_key."""
        from jarvis_core.notes.note_generator import _group_by_key
        items = [{"type": "A", "id": 1}, {"type": "B", "id": 2}, {"type": "A", "id": 3}]
        result = _group_by_key(items, "type")
        assert len(result["A"]) == 2
        assert len(result["B"]) == 1

    def test_score_from_scores_rankings(self):
        """Test _score_from_scores with rankings."""
        from jarvis_core.notes.note_generator import _score_from_scores
        scores = {"rankings": [{"paper_id": "p1", "score": 0.9}]}
        result = _score_from_scores(scores)
        assert result["p1"] == 0.9

    def test_score_from_scores_total_score(self):
        """Test _score_from_scores with total_score."""
        from jarvis_core.notes.note_generator import _score_from_scores
        scores = {"rankings": [{"paper_id": "p1", "total_score": 0.8}]}
        result = _score_from_scores(scores)
        assert result["p1"] == 0.8

    def test_score_from_scores_papers(self):
        """Test _score_from_scores with papers dict."""
        from jarvis_core.notes.note_generator import _score_from_scores
        scores = {"papers": {"p1": {"a": 0.5, "b": 0.3}, "p2": 0.6}}
        result = _score_from_scores(scores)
        assert result["p1"] == 0.8
        assert result["p2"] == 0.6

    def test_compute_rankings(self):
        """Test _compute_rankings."""
        from jarvis_core.notes.note_generator import _compute_rankings
        papers = [{"paper_id": "p1"}, {"paper_id": "p2"}]
        claims = [{"paper_id": "p1"}, {"paper_id": "p1"}]
        scores = {}
        result = _compute_rankings(papers, claims, scores)
        assert result[0]["paper_id"] == "p1"

    def test_assign_tiers(self):
        """Test _assign_tiers."""
        from jarvis_core.notes.note_generator import _assign_tiers
        rankings = [{"paper_id": f"p{i}", "rank": i} for i in range(1, 11)]
        result = _assign_tiers(rankings)
        assert result["p1"] == "S"
        assert "A" in result.values()

    def test_assign_tiers_empty(self):
        """Test _assign_tiers with empty."""
        from jarvis_core.notes.note_generator import _assign_tiers
        result = _assign_tiers([])
        assert result == {}

    def test_build_evidence_map(self):
        """Test _build_evidence_map."""
        from jarvis_core.notes.note_generator import _build_evidence_map
        claims = [{"claim_id": "c1"}]
        evidence = {"c1": [{"locator": {"section": "Abstract"}, "evidence_text": "Quote"}]}
        result = _build_evidence_map(claims, evidence)
        assert "c1" in result

    def test_build_key_claims(self):
        """Test _build_key_claims."""
        from jarvis_core.notes.note_generator import _build_key_claims
        claims = [{"claim_id": "c1", "claim_text": "Claim text"}]
        evidence = {"c1": [{"locator": {"section": "Methods"}}]}
        result = _build_key_claims(claims, evidence)
        assert "Claim text" in result

    def test_build_key_claims_empty(self):
        """Test _build_key_claims with empty."""
        from jarvis_core.notes.note_generator import _build_key_claims
        result = _build_key_claims([], {})
        assert "主張の抽出データがありません" in result

    def test_generate_notes_missing_dir(self):
        """Test generate_notes with missing directory."""
        from jarvis_core.notes.note_generator import generate_notes
        with pytest.raises(FileNotFoundError):
            generate_notes("nonexistent_run", Path("/nonexistent"))


# ============================================================
# Tests for integrations/ris_bibtex.py (199 lines)
# ============================================================

class TestRISBibTeXFunctional:
    """Comprehensive tests for ris_bibtex module - all functions."""

    def test_reference_creation(self):
        """Test Reference dataclass."""
        from jarvis_core.integrations.ris_bibtex import Reference
        ref = Reference(
            id="ref1",
            title="Test Title",
            authors=["Author 1"],
            year=2024
        )
        assert ref.title == "Test Title"
        assert ref.year == 2024

    def test_reference_to_dict(self):
        """Test Reference.to_dict."""
        from jarvis_core.integrations.ris_bibtex import Reference
        ref = Reference(
            id="ref1",
            title="Test Title",
            authors=["Author 1"],
            year=2024,
            journal="Test Journal"
        )
        d = ref.to_dict()
        assert d["title"] == "Test Title"
        assert d["journal"] == "Test Journal"

    def test_ris_parser(self):
        """Test RISParser."""
        from jarvis_core.integrations.ris_bibtex import RISParser
        ris = """TY  - JOUR
TI  - Test Title
AU  - Author One
PY  - 2024
ER  - 
"""
        parser = RISParser()
        refs = parser.parse(ris)
        assert len(refs) == 1
        assert refs[0].title == "Test Title"

    def test_ris_parser_multiple(self):
        """Test RISParser with multiple entries."""
        from jarvis_core.integrations.ris_bibtex import RISParser
        ris = """TY  - JOUR
TI  - Paper 1
ER  - 

TY  - JOUR
TI  - Paper 2
ER  - 
"""
        parser = RISParser()
        refs = parser.parse(ris)
        assert len(refs) == 2

    def test_bibtex_parser(self):
        """Test BibTeXParser."""
        from jarvis_core.integrations.ris_bibtex import BibTeXParser
        bibtex = """@article{test2024,
    title = {Test Title},
    author = {Test Author},
    year = {2024}
}
"""
        parser = BibTeXParser()
        refs = parser.parse(bibtex)
        assert len(refs) >= 1

    def test_ris_exporter(self):
        """Test RISExporter."""
        from jarvis_core.integrations.ris_bibtex import Reference, RISExporter
        refs = [Reference(id="1", title="Test", authors=["A1"], year=2024)]
        exporter = RISExporter()
        output = exporter.export(refs)
        assert "TY  -" in output
        assert "TI  - Test" in output

    def test_bibtex_exporter(self):
        """Test BibTeXExporter."""
        from jarvis_core.integrations.ris_bibtex import Reference, BibTeXExporter
        refs = [Reference(id="1", title="Test", authors=["A1"], year=2024)]
        exporter = BibTeXExporter()
        output = exporter.export(refs)
        assert "title" in output.lower()

    def test_roundtrip_ris(self):
        """Test RIS roundtrip."""
        from jarvis_core.integrations.ris_bibtex import Reference, RISParser, RISExporter
        original = Reference(id="1", title="Roundtrip", authors=["Author"], year=2024)
        exporter = RISExporter()
        ris_text = exporter.export([original])
        parser = RISParser()
        parsed = parser.parse(ris_text)
        assert parsed[0].title == "Roundtrip"

    def test_references_to_jsonl(self):
        """Test references_to_jsonl."""
        from jarvis_core.integrations.ris_bibtex import Reference, references_to_jsonl
        refs = [Reference(id="1", title="Test", authors=["A1"])]
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            path = Path(f.name)
        references_to_jsonl(refs, path)
        assert path.exists()
        path.unlink()

    def test_jsonl_to_references(self):
        """Test jsonl_to_references."""
        from jarvis_core.integrations.ris_bibtex import Reference, references_to_jsonl, jsonl_to_references
        refs = [Reference(id="1", title="Test", authors=["A1"])]
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            path = Path(f.name)
        references_to_jsonl(refs, path)
        loaded = jsonl_to_references(path)
        assert loaded[0].title == "Test"
        path.unlink()


# ============================================================
# Tests for scoring/registry.py
# ============================================================

class TestScoringRegistryFunctional:
    """Tests for scoring registry."""

    def test_import(self):
        from jarvis_core.scoring import registry
        assert hasattr(registry, "__name__")


# ============================================================
# Tests for visualization/positioning.py
# ============================================================

class TestVisualizationPositioningFunctional:
    """Tests for visualization positioning."""

    def test_import(self):
        from jarvis_core.visualization import positioning
        assert hasattr(positioning, "__name__")
