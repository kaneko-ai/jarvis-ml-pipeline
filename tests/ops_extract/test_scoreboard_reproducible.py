from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jarvis_core.ops_extract.scoreboard import generate_weekly_report


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _create_run(base: Path, name: str, *, committed: bool, total_chars: int) -> None:
    run_dir = base / name
    now = datetime.now(timezone.utc).isoformat()
    _write(
        run_dir / "run_metadata.json",
        {
            "mode": "ops_extract",
            "finished_at": now,
            "status": "success",
        },
    )
    _write(run_dir / "manifest.json", {"committed_drive": committed})
    _write(
        run_dir / "metrics.json",
        {"extract": {"total_chars": total_chars, "empty_page_ratio": 0.0}},
    )
    _write(run_dir / "warnings.json", {"warnings": []})


def test_scoreboard_reproducible(tmp_path: Path):
    runs = tmp_path / "runs"
    reports = tmp_path / "reports"
    _create_run(runs, "r1", committed=True, total_chars=1200)
    _create_run(runs, "r2", committed=True, total_chars=900)
    first = generate_weekly_report(runs_base=runs, reports_base=reports)
    second = generate_weekly_report(runs_base=runs, reports_base=reports)
    assert first.ops_score == second.ops_score
    assert first.extract_score == second.extract_score
    assert first.run_count == second.run_count
