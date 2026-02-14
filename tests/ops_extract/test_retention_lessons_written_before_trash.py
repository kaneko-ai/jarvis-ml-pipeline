from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jarvis_core.ops_extract.retention import apply_ops_extract_retention


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_retention_writes_lessons_before_trash(tmp_path: Path):
    runs = tmp_path / "runs"
    runs.mkdir(parents=True)
    lessons = tmp_path / "lessons.md"
    now = datetime(2026, 2, 14, tzinfo=timezone.utc)

    failed_old = runs / "failed_old"
    failed_old.mkdir()
    _write(
        failed_old / "run_metadata.json",
        {
            "mode": "ops_extract",
            "status": "failed",
            "finished_at": (now - timedelta(days=35)).isoformat(),
        },
    )
    _write(failed_old / "manifest.json", {"status": "failed"})
    _write(
        failed_old / "failure_analysis.json",
        {
            "category": "network",
            "root_cause_guess": "timeout",
            "recommendation_steps": ["retry"],
            "preventive_checks": ["check_network_state"],
        },
    )

    result = apply_ops_extract_retention(
        runs_base=runs,
        lessons_path=lessons,
        now=now,
        failed_days=30,
        success_days=180,
        trash_days=7,
    )
    assert "failed_old" in result.moved_to_trash
    text = lessons.read_text(encoding="utf-8")
    assert "run_id=failed_old" in text

