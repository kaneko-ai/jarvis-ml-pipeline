from __future__ import annotations

from pathlib import Path

from scripts.ci_run import generate_summary


def _run_summary(tmp_path: Path, run_id: str, status: str) -> dict:
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    stats = {"meta": 1, "pmcids": 0, "pdf_ok": 0, "chunks": 0}
    return generate_summary(
        run_id,
        "test-query",
        status,
        run_dir,
        "2024-01-01T00:00:00Z",
        "2024-01-01T01:00:00Z",
        stats,
    )


def test_generate_summary_normalizes_status_and_gate_passed(tmp_path: Path) -> None:
    success_summary = _run_summary(tmp_path, "run-success", "complete")
    assert success_summary["status"] == "success"
    assert success_summary["gate_passed"] is True

    failed_summary = _run_summary(tmp_path, "run-failed", "failed")
    assert failed_summary["status"] == "failed"
    assert failed_summary["gate_passed"] is False
