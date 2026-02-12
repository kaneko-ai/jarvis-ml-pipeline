"""Coverage tests for jarvis_core.notes.note_generator."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _write_jsonl(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# ---------------------------------------------------------------------------
# helper-function unit tests
# ---------------------------------------------------------------------------
class TestHelperFunctions:
    """Test internal helper functions."""

    def test_load_json_missing(self, tmp_path: Path) -> None:
        from jarvis_core.notes.note_generator import _load_json

        assert _load_json(tmp_path / "nope.json") == {}

    def test_load_json_exists(self, tmp_path: Path) -> None:
        from jarvis_core.notes.note_generator import _load_json

        p = tmp_path / "data.json"
        _write_json(p, {"key": "value"})
        assert _load_json(p) == {"key": "value"}

    def test_load_jsonl_missing(self, tmp_path: Path) -> None:
        from jarvis_core.notes.note_generator import _load_jsonl

        assert _load_jsonl(tmp_path / "nope.jsonl") == []

    def test_load_jsonl_exists(self, tmp_path: Path) -> None:
        from jarvis_core.notes.note_generator import _load_jsonl

        p = tmp_path / "data.jsonl"
        _write_jsonl(p, [{"a": 1}, {"b": 2}])
        result = _load_jsonl(p)
        assert len(result) == 2
        assert result[0]["a"] == 1

    def test_safe_filename(self) -> None:
        from jarvis_core.notes.note_generator import _safe_filename

        assert _safe_filename("abc/def:ghi") == "abc_def_ghi"
        assert _safe_filename("normal-name.txt") == "normal-name.txt"

    def test_slug(self) -> None:
        from jarvis_core.notes.note_generator import _slug

        assert _slug("Hello World", max_len=10) == "hello_worl"
        assert _slug("") == "untitled"
        assert _slug("test") == "test"

    def test_extract_locator_full(self) -> None:
        from jarvis_core.notes.note_generator import _extract_locator

        loc = {"section": "Methods", "paragraph_index": 1, "sentence_index": 2, "chunk_id": "c1"}
        section, para, sent, chunk = _extract_locator(loc)
        assert section == "Methods"
        assert para == 1
        assert sent == 2
        assert chunk == "c1"

    def test_extract_locator_fallback_keys(self) -> None:
        from jarvis_core.notes.note_generator import _extract_locator

        loc = {"Section": "Results", "paragraph": 3, "sentence": 4, "chunk": "c2"}
        section, para, sent, chunk = _extract_locator(loc)
        assert section == "Results"
        assert para == 3
        assert sent == 4
        assert chunk == "c2"

    def test_extract_locator_empty(self) -> None:
        from jarvis_core.notes.note_generator import _extract_locator

        section, para, sent, chunk = _extract_locator({})
        assert section == "Unknown"
        assert para is None
        assert sent is None
        assert chunk is None

    def test_format_locator(self) -> None:
        from jarvis_core.notes.note_generator import _format_locator

        result = _format_locator(
            {"section": "Intro", "paragraph_index": 0, "sentence_index": 1, "chunk_id": "c0"}
        )
        assert "Evidence:" in result
        assert "Intro" in result

    def test_format_locator_empty(self) -> None:
        from jarvis_core.notes.note_generator import _format_locator

        result = _format_locator({})
        assert "Unknown" in result
        assert "?" in result

    def test_ensure_length_truncate(self) -> None:
        from jarvis_core.notes.note_generator import _ensure_length

        long_text = "a" * 500
        result = _ensure_length(long_text, 10, 100)
        assert len(result) == 100
        assert result.endswith("…")

    def test_ensure_length_pad(self) -> None:
        from jarvis_core.notes.note_generator import _ensure_length

        result = _ensure_length("short", 200, 500)
        assert len(result) >= 200

    def test_ensure_length_ok(self) -> None:
        from jarvis_core.notes.note_generator import _ensure_length

        text = "a" * 50
        result = _ensure_length(text, 10, 100)
        assert result == text

    def test_build_tldr_with_claims(self) -> None:
        from jarvis_core.notes.note_generator import _build_tldr

        paper = {"title": "My Paper"}
        claims = [
            {"claim_text": "Finding A"},
            {"claim_text": "Finding B"},
            {"claim_text": "Finding C"},
        ]
        result = _build_tldr(paper, claims)
        assert "My Paper" in result
        assert len(result) >= 200

    def test_build_tldr_no_claims(self) -> None:
        from jarvis_core.notes.note_generator import _build_tldr

        result = _build_tldr({"title": "Paper"}, [])
        assert "Paper" in result

    def test_build_snapshot_with_value(self) -> None:
        from jarvis_core.notes.note_generator import _build_snapshot

        paper = {"methods": "PCR analysis was performed."}
        assert _build_snapshot("methods", paper, "fallback") == "PCR analysis was performed."

    def test_build_snapshot_fallback(self) -> None:
        from jarvis_core.notes.note_generator import _build_snapshot

        assert _build_snapshot("methods", {}, "fallback") == "fallback"

    def test_build_snapshot_empty_string(self) -> None:
        from jarvis_core.notes.note_generator import _build_snapshot

        assert _build_snapshot("methods", {"methods": "   "}, "fb") == "fb"

    def test_build_limitations_with_value(self) -> None:
        from jarvis_core.notes.note_generator import _build_limitations

        result = _build_limitations({"limitations": "Small sample size"})
        assert "Small sample size" in result

    def test_build_limitations_without(self) -> None:
        from jarvis_core.notes.note_generator import _build_limitations

        result = _build_limitations({})
        assert "限定的" in result

    def test_build_why_it_matters(self) -> None:
        from jarvis_core.notes.note_generator import _build_why_it_matters

        result = _build_why_it_matters({"domain": "Cancer Research"})
        assert "Cancer Research" in result

    def test_build_why_it_matters_no_domain(self) -> None:
        from jarvis_core.notes.note_generator import _build_why_it_matters

        result = _build_why_it_matters({})
        assert "研究テーマ" in result

    def test_group_by_key(self) -> None:
        from jarvis_core.notes.note_generator import _group_by_key

        items = [{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "a", "v": 3}]
        grouped = _group_by_key(items, "k")
        assert len(grouped["a"]) == 2
        assert len(grouped["b"]) == 1

    def test_group_by_key_missing(self) -> None:
        from jarvis_core.notes.note_generator import _group_by_key

        items = [{"v": 1}]
        grouped = _group_by_key(items, "k")
        assert "unknown" in grouped


class TestScoreAndRanking:
    """Test scoring and ranking functions."""

    def test_score_from_scores_rankings_list(self) -> None:
        from jarvis_core.notes.note_generator import _score_from_scores

        scores = {"rankings": [{"paper_id": "p1", "score": 5.0}, {"id": "p2", "total_score": 3.0}]}
        result = _score_from_scores(scores)
        assert result["p1"] == 5.0
        assert result["p2"] == 3.0

    def test_score_from_scores_papers_dict(self) -> None:
        from jarvis_core.notes.note_generator import _score_from_scores

        scores = {"papers": {"p1": {"a": 1.0, "b": 2.0}, "p2": 7.0}}
        result = _score_from_scores(scores)
        assert result["p1"] == 3.0
        assert result["p2"] == 7.0

    def test_score_from_scores_empty(self) -> None:
        from jarvis_core.notes.note_generator import _score_from_scores

        assert _score_from_scores({}) == {}

    def test_compute_rankings(self) -> None:
        from jarvis_core.notes.note_generator import _compute_rankings

        papers = [{"paper_id": "p1"}, {"paper_id": "p2"}]
        scores = {"rankings": [{"paper_id": "p1", "score": 10}, {"paper_id": "p2", "score": 5}]}
        result = _compute_rankings(papers, [], scores)
        assert result[0]["paper_id"] == "p1"
        assert result[0]["rank"] == 1

    def test_compute_rankings_no_scores(self) -> None:
        from jarvis_core.notes.note_generator import _compute_rankings

        papers = [{"paper_id": "p1"}, {"paper_id": "p2"}]
        claims = [{"paper_id": "p1"}, {"paper_id": "p1"}, {"paper_id": "p2"}]
        result = _compute_rankings(papers, claims, {})
        assert result[0]["paper_id"] == "p1"

    def test_assign_tiers_empty(self) -> None:
        from jarvis_core.notes.note_generator import _assign_tiers

        assert _assign_tiers([]) == {}

    def test_assign_tiers_normal(self) -> None:
        from jarvis_core.notes.note_generator import _assign_tiers

        rankings = [{"paper_id": f"p{i}", "rank": i} for i in range(1, 11)]
        tiers = _assign_tiers(rankings)
        assert tiers["p1"] == "S"
        assert any(v == "A" for v in tiers.values())
        assert any(v == "B" for v in tiers.values())

    def test_assign_tiers_small(self) -> None:
        from jarvis_core.notes.note_generator import _assign_tiers

        rankings = [{"paper_id": "p1", "rank": 1}, {"paper_id": "p2", "rank": 2}]
        tiers = _assign_tiers(rankings)
        assert "p1" in tiers
        assert "p2" in tiers


class TestBuildEvidenceAndClaims:
    """Test evidence map and key claims building."""

    def test_build_evidence_map_with_evidence(self) -> None:
        from jarvis_core.notes.note_generator import _build_evidence_map

        claims = [{"claim_id": "c1"}]
        evidence = {"c1": [{"locator": {"section": "Methods"}, "evidence_text": "sample text"}]}
        result = _build_evidence_map(claims, evidence)
        assert "c1" in result
        assert "Methods" in result

    def test_build_evidence_map_no_evidence(self) -> None:
        from jarvis_core.notes.note_generator import _build_evidence_map

        claims = [{"claim_id": "c1"}]
        result = _build_evidence_map(claims, {})
        assert "N/A" in result

    def test_build_evidence_map_bad_locator(self) -> None:
        from jarvis_core.notes.note_generator import _build_evidence_map

        claims = [{"claim_id": "c1"}]
        evidence = {"c1": [{"locator": "not_a_dict", "evidence_text": "data"}]}
        result = _build_evidence_map(claims, evidence)
        assert "Unknown" in result

    def test_build_key_claims_nonempty(self) -> None:
        from jarvis_core.notes.note_generator import _build_key_claims

        claims = [{"claim_id": "c1", "claim_text": "Claim A"}]
        evidence = {"c1": [{"locator": {"section": "Results"}, "evidence_text": "ev text"}]}
        result = _build_key_claims(claims, evidence)
        assert "Claim A" in result

    def test_build_key_claims_no_evidence(self) -> None:
        from jarvis_core.notes.note_generator import _build_key_claims

        claims = [{"claim_id": "c1", "claim_text": "Claim A"}]
        result = _build_key_claims(claims, {})
        assert "Claim A" in result
        assert "Unknown" in result

    def test_build_key_claims_empty(self) -> None:
        from jarvis_core.notes.note_generator import _build_key_claims

        result = _build_key_claims([], {})
        assert "主張の抽出データがありません" in result


class TestGenerateNotes:
    """Test the main generate_notes function."""

    def test_generate_notes_missing_dir(self, tmp_path: Path) -> None:
        from jarvis_core.notes.note_generator import generate_notes

        with pytest.raises(FileNotFoundError):
            generate_notes("nonexistent", source_runs_dir=tmp_path)

    def test_generate_notes_full(self, tmp_path: Path) -> None:
        from jarvis_core.notes.note_generator import generate_notes

        run_id = "test_run"
        run_dir = tmp_path / "runs" / run_id
        run_dir.mkdir(parents=True)

        papers = [
            {
                "paper_id": "p1",
                "title": "Paper One",
                "year": 2024,
                "journal": "J1",
                "doi": "10.1/test",
                "oa_status": "gold",
                "keywords": ["ml"],
                "methods": "Method A",
                "results": "Result A",
                "limitations": "Small N",
                "domain": "AI",
            },
            {"paper_id": "p2", "title": "Paper Two", "year": 2023},
        ]
        claims = [
            {"claim_id": "c1", "paper_id": "p1", "claim_text": "Finding one"},
            {"claim_id": "c2", "paper_id": "p2", "claim_text": "Finding two"},
        ]
        evidence = [
            {
                "claim_id": "c1",
                "evidence_text": "Evidence text one",
                "locator": {
                    "section": "Methods",
                    "paragraph_index": 0,
                    "sentence_index": 1,
                    "chunk_id": "ch1",
                },
            },
        ]
        scores = {"rankings": [{"paper_id": "p1", "score": 10.0}, {"paper_id": "p2", "score": 5.0}]}
        input_data = {"query": "test query", "constraints": {"year": ">2020"}}
        warnings_data = [{"code": "W001"}, {"code": "W001"}, {"code": "W002"}]

        _write_jsonl(run_dir / "papers.jsonl", papers)
        _write_jsonl(run_dir / "claims.jsonl", claims)
        _write_jsonl(run_dir / "evidence.jsonl", evidence)
        _write_json(run_dir / "scores.json", scores)
        _write_json(run_dir / "input.json", input_data)
        _write_jsonl(run_dir / "warnings.jsonl", warnings_data)

        output_dir = tmp_path / "output"
        result = generate_notes(
            run_id, source_runs_dir=tmp_path / "runs", output_base_dir=output_dir
        )

        assert result["papers_count"] == 2
        assert result["claims_count"] == 2
        assert "template_version" in result
        assert (output_dir / run_id / "notes" / "00_RUN_OVERVIEW.md").exists()
        assert (output_dir / run_id / "notes" / "01_TIER_S.md").exists()
        assert (output_dir / run_id / "notes" / "02_TIER_A.md").exists()
        assert (output_dir / run_id / "research_rank.json").exists()

    def test_generate_notes_empty_data(self, tmp_path: Path) -> None:
        from jarvis_core.notes.note_generator import generate_notes

        run_id = "empty_run"
        run_dir = tmp_path / "runs" / run_id
        run_dir.mkdir(parents=True)
        # Create empty files
        _write_jsonl(run_dir / "papers.jsonl", [])
        _write_jsonl(run_dir / "claims.jsonl", [])
        _write_jsonl(run_dir / "evidence.jsonl", [])
        _write_json(run_dir / "scores.json", {})
        _write_json(run_dir / "input.json", {})
        _write_jsonl(run_dir / "warnings.jsonl", [])

        output_dir = tmp_path / "output"
        result = generate_notes(
            run_id, source_runs_dir=tmp_path / "runs", output_base_dir=output_dir
        )
        assert result["papers_count"] == 0
