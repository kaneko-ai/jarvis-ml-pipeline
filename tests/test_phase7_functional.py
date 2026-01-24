"""Phase 7: Detailed Functional Tests for 0% Coverage Modules.

Comprehensive tests that execute actual code paths to increase coverage.
"""

import pytest
import tempfile
from pathlib import Path
import json


# ============================================================
# Tests for notes/note_generator.py - Functional Tests
# ============================================================


class TestNoteGeneratorFunctional:
    """Functional tests for note generator module."""

    def test_load_json_existing_file(self):
        from jarvis_core.notes.note_generator import _load_json

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            result = _load_json(Path(f.name))
            assert result == {"key": "value"}

    def test_load_json_nonexistent_file(self):
        from jarvis_core.notes.note_generator import _load_json

        result = _load_json(Path("/nonexistent/path.json"))
        assert result == {}

    def test_load_jsonl_existing_file(self):
        from jarvis_core.notes.note_generator import _load_jsonl

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"id": 1}\n{"id": 2}\n{"id": 3}\n')
            f.flush()
            result = _load_jsonl(Path(f.name))
            assert len(result) == 3
            assert result[0]["id"] == 1

    def test_load_jsonl_nonexistent_file(self):
        from jarvis_core.notes.note_generator import _load_jsonl

        result = _load_jsonl(Path("/nonexistent/path.jsonl"))
        assert result == []

    def test_safe_filename_special_chars(self):
        from jarvis_core.notes.note_generator import _safe_filename

        result = _safe_filename("Test/File:Name?With*Special<Chars>")
        assert "/" not in result
        assert ":" not in result
        assert "?" not in result
        assert "*" not in result

    def test_safe_filename_normal(self):
        from jarvis_core.notes.note_generator import _safe_filename

        result = _safe_filename("normal_filename-123.txt")
        assert result == "normal_filename-123.txt"

    def test_slug_basic(self):
        from jarvis_core.notes.note_generator import _slug

        result = _slug("Hello World Test")
        assert result == "hello_world_test"

    def test_slug_max_length(self):
        from jarvis_core.notes.note_generator import _slug

        long_text = "A" * 100
        result = _slug(long_text, max_len=20)
        assert len(result) == 20

    def test_slug_empty_becomes_untitled(self):
        from jarvis_core.notes.note_generator import _slug

        result = _slug("!@#$%")  # All special chars
        assert result == "untitled"

    def test_extract_locator_complete(self):
        from jarvis_core.notes.note_generator import _extract_locator

        locator = {
            "section": "Methods",
            "paragraph_index": 2,
            "sentence_index": 3,
            "chunk_id": "chunk_001",
        }
        section, paragraph, sentence, chunk_id = _extract_locator(locator)
        assert section == "Methods"
        assert paragraph == 2
        assert sentence == 3
        assert chunk_id == "chunk_001"

    def test_extract_locator_alternate_keys(self):
        from jarvis_core.notes.note_generator import _extract_locator

        locator = {"Section": "Results", "paragraph": 1, "sentence": 5, "chunk": "chunk_002"}
        section, paragraph, sentence, chunk_id = _extract_locator(locator)
        assert section == "Results"
        assert paragraph == 1
        assert sentence == 5
        assert chunk_id == "chunk_002"

    def test_format_locator(self):
        from jarvis_core.notes.note_generator import _format_locator

        locator = {
            "section": "Abstract",
            "paragraph_index": 0,
            "sentence_index": 1,
            "chunk_id": "c1",
        }
        result = _format_locator(locator)
        assert "Evidence:" in result
        assert "Abstract" in result

    def test_ensure_length_too_long(self):
        from jarvis_core.notes.note_generator import _ensure_length

        long_text = "A" * 500
        result = _ensure_length(long_text, min_len=10, max_len=100)
        assert len(result) <= 100
        assert result.endswith("…")

    def test_ensure_length_too_short(self):
        from jarvis_core.notes.note_generator import _ensure_length

        short_text = "Short"
        result = _ensure_length(short_text, min_len=50, max_len=200)
        assert len(result) >= 50

    def test_ensure_length_within_range(self):
        from jarvis_core.notes.note_generator import _ensure_length

        text = "A" * 50
        result = _ensure_length(text, min_len=10, max_len=100)
        assert result == text

    def test_build_tldr_with_claims(self):
        from jarvis_core.notes.note_generator import _build_tldr

        paper = {"title": "Test Paper"}
        claims = [
            {"claim_text": "Claim one about research"},
            {"claim_text": "Claim two about findings"},
        ]
        result = _build_tldr(paper, claims)
        assert "Test Paper" in result
        assert len(result) >= 200

    def test_build_tldr_without_claims(self):
        from jarvis_core.notes.note_generator import _build_tldr

        paper = {"title": "Another Paper"}
        claims = []
        result = _build_tldr(paper, claims)
        assert "Another Paper" in result

    def test_build_snapshot_with_value(self):
        from jarvis_core.notes.note_generator import _build_snapshot

        paper = {"methods": "We used machine learning algorithms."}
        result = _build_snapshot("methods", paper, "No methods")
        assert result == "We used machine learning algorithms."

    def test_build_snapshot_fallback(self):
        from jarvis_core.notes.note_generator import _build_snapshot

        paper = {}
        result = _build_snapshot("methods", paper, "Fallback text")
        assert result == "Fallback text"

    def test_build_limitations_with_author(self):
        from jarvis_core.notes.note_generator import _build_limitations

        paper = {"limitations": "Small sample size"}
        result = _build_limitations(paper)
        assert "Small sample size" in result
        assert "著者の限界" in result

    def test_build_limitations_without_author(self):
        from jarvis_core.notes.note_generator import _build_limitations

        paper = {}
        result = _build_limitations(paper)
        assert "著者の限界" in result

    def test_build_why_it_matters(self):
        from jarvis_core.notes.note_generator import _build_why_it_matters

        paper = {"domain": "Cancer Research"}
        result = _build_why_it_matters(paper)
        assert "Cancer Research" in result

    def test_group_by_key(self):
        from jarvis_core.notes.note_generator import _group_by_key

        items = [
            {"type": "A", "id": 1},
            {"type": "B", "id": 2},
            {"type": "A", "id": 3},
            {"type": "C", "id": 4},
        ]
        result = _group_by_key(items, "type")
        assert len(result["A"]) == 2
        assert len(result["B"]) == 1
        assert len(result["C"]) == 1

    def test_score_from_scores_rankings(self):
        from jarvis_core.notes.note_generator import _score_from_scores

        scores = {"rankings": [{"paper_id": "p1", "score": 0.9}, {"paper_id": "p2", "score": 0.7}]}
        result = _score_from_scores(scores)
        assert result["p1"] == 0.9
        assert result["p2"] == 0.7

    def test_score_from_scores_total_score(self):
        from jarvis_core.notes.note_generator import _score_from_scores

        scores = {"rankings": [{"paper_id": "p1", "total_score": 0.8}]}
        result = _score_from_scores(scores)
        assert result["p1"] == 0.8

    def test_score_from_scores_papers(self):
        from jarvis_core.notes.note_generator import _score_from_scores

        scores = {"papers": {"p1": {"relevance": 0.5, "quality": 0.3}, "p2": 0.6}}
        result = _score_from_scores(scores)
        assert result["p1"] == 0.8
        assert result["p2"] == 0.6

    def test_compute_rankings(self):
        from jarvis_core.notes.note_generator import _compute_rankings

        papers = [{"paper_id": "p1"}, {"paper_id": "p2"}]
        claims = [{"paper_id": "p1"}, {"paper_id": "p1"}, {"paper_id": "p2"}]
        scores = {}
        result = _compute_rankings(papers, claims, scores)
        assert len(result) == 2
        assert result[0]["paper_id"] == "p1"  # More claims = higher score

    def test_assign_tiers(self):
        from jarvis_core.notes.note_generator import _assign_tiers

        rankings = [
            {"paper_id": "p1", "rank": 1, "score": 10},
            {"paper_id": "p2", "rank": 2, "score": 9},
            {"paper_id": "p3", "rank": 3, "score": 8},
            {"paper_id": "p4", "rank": 4, "score": 7},
            {"paper_id": "p5", "rank": 5, "score": 6},
            {"paper_id": "p6", "rank": 6, "score": 5},
            {"paper_id": "p7", "rank": 7, "score": 4},
            {"paper_id": "p8", "rank": 8, "score": 3},
            {"paper_id": "p9", "rank": 9, "score": 2},
            {"paper_id": "p10", "rank": 10, "score": 1},
        ]
        result = _assign_tiers(rankings)
        assert result["p1"] == "S"  # Top 10%
        assert "A" in result.values()
        assert "B" in result.values()

    def test_assign_tiers_empty(self):
        from jarvis_core.notes.note_generator import _assign_tiers

        result = _assign_tiers([])
        assert result == {}

    def test_build_evidence_map(self):
        from jarvis_core.notes.note_generator import _build_evidence_map

        claims = [{"claim_id": "c1"}, {"claim_id": "c2"}]
        evidence_by_claim = {
            "c1": [{"locator": {"section": "Abstract"}, "evidence_text": "Quote 1"}],
            "c2": [],
        }
        result = _build_evidence_map(claims, evidence_by_claim)
        assert "c1" in result
        assert "Quote 1" in result

    def test_build_key_claims(self):
        from jarvis_core.notes.note_generator import _build_key_claims

        claims = [
            {"claim_id": "c1", "claim_text": "This is claim one."},
            {"claim_id": "c2", "claim_text": "This is claim two."},
        ]
        evidence_by_claim = {"c1": [{"locator": {"section": "Methods"}}]}
        result = _build_key_claims(claims, evidence_by_claim)
        assert "claim one" in result
        assert "claim two" in result

    def test_build_key_claims_empty(self):
        from jarvis_core.notes.note_generator import _build_key_claims

        result = _build_key_claims([], {})
        assert "主張の抽出データがありません" in result

    def test_generate_notes_missing_directory(self):
        from jarvis_core.notes.note_generator import generate_notes

        with pytest.raises(FileNotFoundError):
            generate_notes("nonexistent_run_id", Path("/nonexistent"))


# ============================================================
# Tests for integrations/ris_bibtex.py - Functional Tests
# ============================================================


class TestRISBibTeXFunctional:
    """Functional tests for RIS/BibTeX module."""

    def test_reference_creation_full(self):
        from jarvis_core.integrations.ris_bibtex import Reference

        ref = Reference(
            id="ref001",
            title="Machine Learning in Healthcare",
            authors=["John Doe", "Jane Smith"],
            year=2024,
            journal="Nature Medicine",
            volume="10",
            issue="5",
            pages="100-120",
            doi="10.1234/nm.2024.001",
            pmid="12345678",
            abstract="This is an abstract.",
            keywords=["ML", "Healthcare"],
            url="https://example.com/paper",
        )
        d = ref.to_dict()
        assert d["title"] == "Machine Learning in Healthcare"
        assert d["year"] == 2024
        assert len(d["authors"]) == 2

    def test_ris_parser_complete_entry(self):
        from jarvis_core.integrations.ris_bibtex import RISParser

        ris = """TY  - JOUR
TI  - Test Title
AU  - Smith, John
AU  - Doe, Jane
PY  - 2024
JO  - Test Journal
VL  - 10
IS  - 5
SP  - 100
EP  - 120
DO  - 10.1234/test
AB  - This is the abstract text.
KW  - keyword1
KW  - keyword2
UR  - https://example.com
ER  - 
"""
        parser = RISParser()
        refs = parser.parse(ris)
        assert len(refs) == 1
        assert refs[0].title == "Test Title"
        assert len(refs[0].authors) == 2

    def test_ris_parser_multiple_entries(self):
        from jarvis_core.integrations.ris_bibtex import RISParser

        ris = """TY  - JOUR
TI  - First Paper
AU  - Author One
ER  - 

TY  - JOUR
TI  - Second Paper
AU  - Author Two
ER  - 

TY  - JOUR
TI  - Third Paper
AU  - Author Three
ER  - 
"""
        parser = RISParser()
        refs = parser.parse(ris)
        assert len(refs) == 3

    def test_bibtex_parser_complete_entry(self):
        from jarvis_core.integrations.ris_bibtex import BibTeXParser

        bibtex = """@article{smith2024test,
    title = {Test Title for BibTeX},
    author = {Smith, John and Doe, Jane},
    year = {2024},
    journal = {Journal of Testing},
    volume = {15},
    number = {3},
    pages = {50-75},
    doi = {10.1234/bibtex}
}
"""
        parser = BibTeXParser()
        refs = parser.parse(bibtex)
        assert len(refs) >= 1

    def test_ris_exporter_full(self):
        from jarvis_core.integrations.ris_bibtex import Reference, RISExporter

        refs = [
            Reference(
                id="1",
                title="Export Test Paper",
                authors=["Test Author"],
                year=2024,
                journal="Test Journal",
                volume="5",
                pages="1-10",
                doi="10.1234/export",
            )
        ]
        exporter = RISExporter()
        output = exporter.export(refs)
        assert "TY  -" in output
        assert "TI  - Export Test Paper" in output
        assert "AU  - Test Author" in output
        assert "ER  -" in output

    def test_bibtex_exporter_full(self):
        from jarvis_core.integrations.ris_bibtex import Reference, BibTeXExporter

        refs = [
            Reference(
                id="2",
                title="BibTeX Export Test",
                authors=["Smith, John"],
                year=2024,
                journal="Export Journal",
            )
        ]
        exporter = BibTeXExporter()
        output = exporter.export(refs)
        assert "@article" in output or "@misc" in output
        assert "BibTeX Export Test" in output

    def test_import_export_ris_roundtrip(self):
        from jarvis_core.integrations.ris_bibtex import Reference, RISParser, RISExporter

        original = Reference(
            id="rt1", title="Roundtrip Test", authors=["Roundtrip Author"], year=2024
        )
        exporter = RISExporter()
        ris_text = exporter.export([original])
        parser = RISParser()
        parsed = parser.parse(ris_text)
        assert len(parsed) >= 1
        assert parsed[0].title == "Roundtrip Test"

    def test_references_to_jsonl_and_back(self):
        from jarvis_core.integrations.ris_bibtex import (
            Reference,
            references_to_jsonl,
            jsonl_to_references,
        )

        refs = [
            Reference(id="j1", title="JSONL Test 1", authors=["A1"]),
            Reference(id="j2", title="JSONL Test 2", authors=["A2"]),
        ]
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = Path(f.name)
        references_to_jsonl(refs, path)
        loaded = jsonl_to_references(path)
        assert len(loaded) == 2
        assert loaded[0].title == "JSONL Test 1"


# ============================================================
# Tests for pipelines/paper_pipeline.py - Functional Tests
# ============================================================


class TestPaperPipelineFunctional:
    """Functional tests for paper pipeline module."""

    def test_index_meta_to_dict_complete(self):
        from jarvis_core.pipelines.paper_pipeline import IndexMeta

        meta = IndexMeta(
            index_id="idx_001",
            created_at="2024-01-01T00:00:00Z",
            source_path="/data/papers",
            chunk_strategy="adaptive",
            chunk_count=500,
            paper_count=50,
        )
        d = meta.to_dict()
        assert d["index_id"] == "idx_001"
        assert d["chunk_strategy"] == "adaptive"
        assert d["chunk_count"] == 500

    def test_paper_source_to_dict_complete(self):
        from jarvis_core.pipelines.paper_pipeline import PaperSource

        source = PaperSource(
            paper_id="paper_001",
            title="Test Paper Title",
            source="pubmed",
            doi="10.1234/test.001",
            pmid="12345678",
            url="https://pubmed.ncbi.nlm.nih.gov/12345678",
            fulltext_available=True,
        )
        d = source.to_dict()
        assert d["paper_id"] == "paper_001"
        assert d["fulltext_available"] is True
        assert d["doi"] == "10.1234/test.001"

    def test_pipeline_create_and_load_index(self):
        from jarvis_core.pipelines.paper_pipeline import PaperPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = PaperPipeline(indexes_dir=tmpdir)

            # Create index
            papers = [{"paper_id": f"p{i}", "title": f"Paper {i}"} for i in range(5)]
            chunks = [{"chunk_id": f"c{i}", "text": f"Chunk {i}"} for i in range(20)]

            meta = pipeline.create_index(
                index_id="test_idx",
                source_path="/source/path",
                papers=papers,
                chunks=chunks,
                chunk_strategy="semantic",
            )

            assert meta.paper_count == 5
            assert meta.chunk_count == 20
            assert meta.chunk_strategy == "semantic"

            # Check index exists
            assert pipeline.check_index("test_idx")

            # Load index meta
            loaded_meta = pipeline.load_index_meta("test_idx")
            assert loaded_meta is not None
            assert loaded_meta.index_id == "test_idx"

    def test_pipeline_process_papers_no_index(self):
        from jarvis_core.pipelines.paper_pipeline import PaperPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = PaperPipeline(indexes_dir=tmpdir, require_index=False)
            result = pipeline.process_papers(query="cancer treatment")
            assert "papers" in result
            assert "claims" in result
            assert "evidence" in result

    def test_pipeline_process_papers_missing_index_warning(self):
        from jarvis_core.pipelines.paper_pipeline import PaperPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = PaperPipeline(indexes_dir=tmpdir, require_index=True)
            result = pipeline.process_papers(query="test query", index_id="nonexistent_index")
            # Should have a warning about missing index
            warnings = result.get("warnings", [])
            assert any(w.get("code") == "INDEX_MISSING" for w in warnings)

    def test_pipeline_record_sources(self):
        from jarvis_core.pipelines.paper_pipeline import PaperPipeline

        pipeline = PaperPipeline()

        # Record multiple sources
        pipeline.record_paper_source("p1", "Paper 1", "pubmed", doi="10.1234/p1")
        pipeline.record_paper_source("p2", "Paper 2", "arxiv", url="https://arxiv.org/abs/1234")
        pipeline.record_paper_source("p3", "Paper 3", "local", fulltext_available=True)

        assert len(pipeline.papers_used) == 3
        summary = pipeline.get_sources_summary()
        assert summary["papers_used"] == 3
        assert len(summary["papers_sources"]) == 3

    def test_pipeline_record_fetch_errors(self):
        from jarvis_core.pipelines.paper_pipeline import PaperPipeline

        pipeline = PaperPipeline()

        pipeline.record_fetch_error("p1", "Connection timeout", retry_count=0)
        pipeline.record_fetch_error("p1", "Connection timeout", retry_count=1)
        pipeline.record_fetch_error("p2", "404 Not Found", retry_count=0)

        summary = pipeline.get_sources_summary()
        assert len(summary["fetch_errors"]) == 3
