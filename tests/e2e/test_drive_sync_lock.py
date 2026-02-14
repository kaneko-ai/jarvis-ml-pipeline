from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from jarvis_core.ops_extract.drive_sync import sync_run_to_drive


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _setup_run_dir(run_dir: Path) -> None:
    _write(run_dir / "result.json", "{}")
    _write(run_dir / "scores.json", "{}")
    _write(run_dir / "metrics.json", "{}")
    _write(
        run_dir / "manifest.json",
        '{"schema_version":"ops_extract_contract_v2","run_id":"r1","project":"demo","created_at":"2026-02-13T00:00:00+00:00","finished_at":"2026-02-13T00:00:00+00:00","status":"success","inputs":[],"outputs":[],"extract":{"method":"pdf_text","needs_ocr":false,"needs_ocr_reason":"not_needed","total_chars":0,"chars_per_page_mean":0.0,"empty_page_ratio":0.0},"ops":{"retries":0,"resume_count":0,"sync_state":"not_started"},"committed":true,"committed_local":true,"committed_drive":false,"version":"ops_extract_v1"}',
    )


def test_drive_sync_lock_conflict_returns_deferred(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    _setup_run_dir(run_dir)
    lock_path = run_dir / ".sync_lock.json"
    lock_path.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "pid": 123,
                "ttl_sec": 600,
            }
        ),
        encoding="utf-8",
    )

    state = sync_run_to_drive(
        run_dir=run_dir,
        enabled=True,
        dry_run=False,
        upload_workers=1,
        access_token="token",
    )

    assert state["state"] == "deferred"
    assert state["last_error"] == "sync_lock_conflict"


def test_drive_sync_lock_ttl_expired_allows_sync(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    _setup_run_dir(run_dir)
    lock_path = run_dir / ".sync_lock.json"
    lock_path.write_text(
        json.dumps(
            {
                "created_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "pid": 123,
                "ttl_sec": 1,
            }
        ),
        encoding="utf-8",
    )

    with patch(
        "jarvis_core.ops_extract.drive_client.DriveResumableClient.upload_bytes",
        return_value={"file_id": "f1", "session_uri": "s1", "attempts": 1},
    ):
        state = sync_run_to_drive(
            run_dir=run_dir,
            enabled=True,
            dry_run=False,
            upload_workers=1,
            access_token="token",
            verify_sha256=False,
            sync_lock_ttl_sec=1,
        )

    assert state["state"] == "committed"
    assert not lock_path.exists()
