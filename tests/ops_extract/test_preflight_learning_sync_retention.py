from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.drive_sync import sync_run_to_drive
from jarvis_core.ops_extract.learning import lesson_exists_for_run, load_block_rules, record_lesson
from jarvis_core.ops_extract.preflight import run_preflight_checks
from jarvis_core.ops_extract.retention import apply_ops_extract_retention


def test_learning_record_and_block_rules(tmp_path: Path):
    lessons = tmp_path / "lessons.md"
    record_lesson(
        run_id="run-a",
        category="ocr",
        root_cause="yomitoku missing",
        recommendation_steps=["install yomitoku"],
        preventive_checks=["check_yomitoku_available"],
        lessons_path=lessons,
    )
    assert lessons.exists()
    assert lesson_exists_for_run("run-a", lessons_path=lessons)

    rules = load_block_rules(lessons)
    assert rules == ["check_yomitoku_available"]


def test_preflight_fails_for_missing_input(tmp_path: Path):
    cfg = OpsExtractConfig(enabled=True, min_disk_free_gb=0.0)
    report = run_preflight_checks(
        input_paths=[tmp_path / "missing.pdf"],
        config=cfg,
        lessons_path=tmp_path / "lessons.md",
    )

    assert report.passed is False
    assert any("check_input_exists" in err for err in report.errors)


def test_preflight_honors_lesson_rule(tmp_path: Path, monkeypatch):
    pdf = tmp_path / "input.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    lessons = tmp_path / "lessons.md"
    lessons.write_text(
        "# Lessons Learned\n\n- block_rule: check_yomitoku_available\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("jarvis_core.ops_extract.preflight.check_yomitoku_available", lambda: False)

    cfg = OpsExtractConfig(enabled=True, min_disk_free_gb=0.0)
    report = run_preflight_checks(input_paths=[pdf], config=cfg, lessons_path=lessons)

    assert report.passed is False
    assert any("check_yomitoku_available" in err for err in report.errors)


def test_preflight_warn_mode_downgrades_hard_rule(tmp_path: Path, monkeypatch):
    pdf = tmp_path / "input.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    lessons = tmp_path / "lessons.md"
    lessons.write_text(
        "# Lessons Learned\n\n- block_rule: hard:check_yomitoku_available\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("jarvis_core.ops_extract.preflight.check_yomitoku_available", lambda: False)

    cfg = OpsExtractConfig(enabled=True, min_disk_free_gb=0.0, preflight_rule_mode="warn")
    report = run_preflight_checks(input_paths=[pdf], config=cfg, lessons_path=lessons)

    assert report.passed is True
    assert any("check_yomitoku_available" in msg for msg in report.warnings)


def test_sync_run_to_drive_disabled(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)

    result = sync_run_to_drive(
        run_dir=run_dir,
        enabled=False,
        dry_run=True,
        upload_workers=2,
    )

    assert result["state"] == "not_started"
    assert (run_dir / "sync_state.json").exists()


def test_sync_run_to_drive_dry_run_committed(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "result.json").write_text("{}", encoding="utf-8")
    (run_dir / "manifest.json").write_text("{}", encoding="utf-8")
    (run_dir / "metrics.json").write_text("{}", encoding="utf-8")

    result = sync_run_to_drive(
        run_dir=run_dir,
        enabled=True,
        dry_run=True,
        upload_workers=2,
    )

    assert result["state"] == "committed"
    assert result["manifest_committed_drive"] is True
    assert len(result["uploaded_files"]) >= 1


def test_sync_run_to_drive_fails_without_token(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "result.json").write_text("{}", encoding="utf-8")

    result = sync_run_to_drive(
        run_dir=run_dir,
        enabled=True,
        dry_run=False,
        upload_workers=1,
        access_token=None,
    )

    assert result["state"] == "failed"
    assert "token" in result["last_error"].lower()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_retention_moves_old_runs_and_cleans_trash(tmp_path: Path):
    runs_base = tmp_path / "runs"
    runs_base.mkdir(parents=True)
    lessons = tmp_path / "lessons.md"

    now = datetime(2026, 2, 13, tzinfo=timezone.utc)
    old_failed = (now - timedelta(days=40)).isoformat()
    old_success = (now - timedelta(days=200)).isoformat()

    failed_run = runs_base / "failed_old"
    failed_run.mkdir(parents=True)
    _write_json(
        failed_run / "run_metadata.json",
        {
            "mode": "ops_extract",
            "status": "failed",
            "finished_at": old_failed,
        },
    )
    _write_json(failed_run / "manifest.json", {"status": "failed", "finished_at": old_failed})
    _write_json(failed_run / "failure_analysis.json", {"category": "ocr"})
    record_lesson(
        run_id="failed_old",
        category="ocr",
        root_cause="ocr unavailable",
        recommendation_steps=["install"],
        preventive_checks=["check_yomitoku_available"],
        lessons_path=lessons,
    )

    success_run = runs_base / "success_old"
    success_run.mkdir(parents=True)
    _write_json(
        success_run / "run_metadata.json",
        {
            "mode": "ops_extract",
            "status": "success",
            "finished_at": old_success,
        },
    )
    _write_json(success_run / "manifest.json", {"status": "success", "finished_at": old_success})

    keep_run = runs_base / "success_recent"
    keep_run.mkdir(parents=True)
    _write_json(
        keep_run / "run_metadata.json",
        {
            "mode": "ops_extract",
            "status": "success",
            "finished_at": now.isoformat(),
        },
    )
    _write_json(keep_run / "manifest.json", {"status": "success", "finished_at": now.isoformat()})

    result = apply_ops_extract_retention(
        runs_base=runs_base,
        lessons_path=lessons,
        now=now,
        failed_days=30,
        success_days=180,
        trash_days=7,
    )

    assert sorted(result.moved_to_trash) == ["failed_old", "success_old"]
    assert result.kept == ["success_recent"]

    trash_candidate = runs_base / "_trash_candidates" / "success_old"
    old_ts = (now - timedelta(days=10)).timestamp()
    os.utime(trash_candidate, (old_ts, old_ts))

    result2 = apply_ops_extract_retention(
        runs_base=runs_base,
        lessons_path=lessons,
        now=now,
        failed_days=30,
        success_days=180,
        trash_days=7,
    )

    assert "success_old" in result2.deleted_from_trash


def test_retention_dry_run_does_not_move_or_delete(tmp_path: Path):
    runs_base = tmp_path / "runs"
    runs_base.mkdir(parents=True)
    lessons = tmp_path / "lessons.md"
    now = datetime(2026, 2, 13, tzinfo=timezone.utc)
    old_success = (now - timedelta(days=200)).isoformat()

    run_dir = runs_base / "success_old"
    run_dir.mkdir(parents=True)
    _write_json(
        run_dir / "run_metadata.json",
        {"mode": "ops_extract", "status": "success", "finished_at": old_success},
    )
    _write_json(run_dir / "manifest.json", {"status": "success", "finished_at": old_success})

    result = apply_ops_extract_retention(
        runs_base=runs_base,
        lessons_path=lessons,
        now=now,
        success_days=180,
        dry_run=True,
    )

    assert "success_old" in result.moved_to_trash
    assert result.dry_run is True
    assert run_dir.exists()


def test_retention_respects_max_delete_per_run(tmp_path: Path):
    runs_base = tmp_path / "runs"
    trash = runs_base / "_trash_candidates"
    trash.mkdir(parents=True)
    now = datetime(2026, 2, 13, tzinfo=timezone.utc)

    for name in ["a", "b", "c"]:
        target = trash / name
        target.mkdir(parents=True)
        old_ts = (now - timedelta(days=10)).timestamp()
        os.utime(target, (old_ts, old_ts))

    result = apply_ops_extract_retention(
        runs_base=runs_base,
        now=now,
        trash_days=7,
        max_delete_per_run=1,
    )

    assert len(result.deleted_from_trash) == 1
