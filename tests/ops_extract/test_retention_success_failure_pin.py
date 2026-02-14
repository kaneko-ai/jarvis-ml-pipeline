from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jarvis_core.ops_extract.retention import apply_ops_extract_retention


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_retention_success_failure_and_pin(tmp_path: Path):
    runs = tmp_path / "runs"
    runs.mkdir(parents=True)
    lessons = tmp_path / "lessons.md"
    now = datetime(2026, 2, 14, tzinfo=timezone.utc)

    success_old = runs / "success_old"
    success_old.mkdir()
    _write(
        success_old / "run_metadata.json",
        {
            "mode": "ops_extract",
            "status": "success",
            "finished_at": (now - timedelta(days=200)).isoformat(),
        },
    )
    _write(success_old / "manifest.json", {"status": "success"})

    failed_old = runs / "failed_old"
    failed_old.mkdir()
    _write(
        failed_old / "run_metadata.json",
        {
            "mode": "ops_extract",
            "status": "failed",
            "finished_at": (now - timedelta(days=40)).isoformat(),
        },
    )
    _write(failed_old / "manifest.json", {"status": "failed"})
    _write(
        failed_old / "failure_analysis.json",
        {
            "category": "ocr",
            "root_cause_guess": "yomitoku_missing",
            "recommendation_steps": ["install yomitoku"],
            "preventive_checks": ["check_yomitoku_available"],
        },
    )

    pinned = runs / "pinned_old"
    pinned.mkdir()
    _write(
        pinned / "run_metadata.json",
        {
            "mode": "ops_extract",
            "status": "success",
            "finished_at": (now - timedelta(days=300)).isoformat(),
            "pinned": True,
        },
    )
    _write(pinned / "manifest.json", {"status": "success"})
    (pinned / ".pin").write_text("1\n", encoding="utf-8")

    result = apply_ops_extract_retention(
        runs_base=runs,
        lessons_path=lessons,
        now=now,
        failed_days=30,
        success_days=180,
        trash_days=7,
    )
    assert "success_old" in result.moved_to_trash
    assert "failed_old" in result.moved_to_trash
    assert "pinned_old" in result.kept
