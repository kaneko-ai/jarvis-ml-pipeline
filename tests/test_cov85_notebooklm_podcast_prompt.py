from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis_core.notebooklm import podcast_prompt as pp


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_claim_lines_with_and_without_evidence() -> None:
    claims = [{"claim_id": "c1", "claim_text": "T cell increases response"}]
    evidence = {"c1": [{"locator": {"section": "Results", "paragraph": 2, "sentence": 1}}]}

    lines = pp._claim_lines(claims, evidence)
    assert len(lines) == 1
    assert "T cell increases response" in lines[0]

    assert pp._claim_lines([{"claim_id": "x", "claim_text": ""}], {})[0].startswith("- ")


def test_prompt_builders_include_core_fields() -> None:
    paper = {"paper_id": "p1", "title": "Checkpoint Study", "journal": "JX", "year": 2025}
    claims = [{"claim_id": "c1", "claim_text": "PD-1 blockade is effective"}]
    evidence_by_claim = {
        "c1": [{"locator": {"section": "Abstract", "paragraph": 1, "sentence": 2}}]
    }

    single = pp.build_single_paper_prompt(paper, claims, evidence_by_claim)
    assert "Checkpoint Study" in single
    assert "PD-1 blockade is effective" in single

    multi = pp.build_multi_paper_prompt([paper], {"p1": claims}, evidence_by_claim)
    outline = pp.build_script_outline([paper], {"p1": claims}, evidence_by_claim)
    assert "Checkpoint Study" in multi
    assert "Podcast Script Outline" in outline


def test_generate_notebooklm_outputs_raises_on_missing_run_dir(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        pp.generate_notebooklm_outputs(
            run_id="missing-run",
            source_runs_dir=tmp_path / "logs" / "runs",
            output_base_dir=tmp_path / "data" / "runs",
        )


def test_generate_notebooklm_outputs_writes_files_and_fallbacks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_id = "run-001"
    source_runs = tmp_path / "logs" / "runs"
    run_dir = source_runs / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    papers = [
        {"paper_id": "p1", "title": "Paper One", "year": 2024, "journal": "J1"},
        {"paper_id": "p2", "title": "Paper Two", "year": 2023, "journal": "J2"},
    ]
    claims = [
        {"claim_id": "c1", "paper_id": "p1", "claim_text": "Claim 1"},
        {"claim_id": "c2", "paper_id": "p2", "claim_text": "Claim 2"},
    ]
    evidence = [
        {"claim_id": "c1", "locator": {"section": "Results", "paragraph": 2, "sentence": 3}},
        {"claim_id": "c2", "locator": {"section": "Methods", "paragraph": 1, "sentence": 1}},
    ]

    _write_jsonl(run_dir / "papers.jsonl", papers)
    _write_jsonl(run_dir / "claims.jsonl", claims)
    _write_jsonl(run_dir / "evidence.jsonl", evidence)
    (run_dir / "scores.json").write_text(json.dumps({"rankings": []}), encoding="utf-8")

    # Force fallback path: when no S/A paper is selected, use all papers.
    monkeypatch.setattr(pp, "_compute_rankings", lambda p, c, s: [{"paper_id": "p1", "rank": 1}])
    monkeypatch.setattr(pp, "_assign_tiers", lambda rankings: {"p1": "B"})

    output = pp.generate_notebooklm_outputs(
        run_id=run_id,
        source_runs_dir=source_runs,
        output_base_dir=tmp_path / "data" / "runs",
    )

    out_dir = tmp_path / "data" / "runs" / run_id / "notebooklm"
    assert output["notebooklm_dir"] == str(out_dir)
    assert output["papers_count"] == 2

    one = (out_dir / "podcast_prompt_1paper.txt").read_text(encoding="utf-8")
    multi = (out_dir / "podcast_prompt_3to5papers.txt").read_text(encoding="utf-8")
    outline = (out_dir / "podcast_script_outline.md").read_text(encoding="utf-8")
    assert "Paper One" in one
    assert "Paper Two" in multi
    assert "Podcast Script Outline" in outline
