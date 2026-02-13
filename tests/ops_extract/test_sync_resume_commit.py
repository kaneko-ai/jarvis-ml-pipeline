from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.ops_extract.drive_sync import sync_run_to_drive


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _setup_run_dir(run_dir: Path) -> None:
    _write(run_dir / "result.json", "{}")
    _write(run_dir / "scores.json", "{}")
    _write(run_dir / "metrics.json", "{}")
    _write(run_dir / "manifest.json", '{"run_id":"r1","committed":true}')


def test_sync_manifest_committed_final(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    _setup_run_dir(run_dir)

    state = sync_run_to_drive(
        run_dir=run_dir,
        enabled=True,
        dry_run=True,
        upload_workers=2,
    )

    assert state["state"] == "committed"
    assert state["manifest_committed_drive"] is True
    assert "version" in state
    assert "pending_files" in state
    assert "failed_files" in state


def test_sync_resume_uploads_failed_only(tmp_path: Path, monkeypatch):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    _setup_run_dir(run_dir)

    result_path = run_dir / "result.json"
    metrics_path = run_dir / "metrics.json"
    previous_state = {
        "version": "ops_extract_sync_v1",
        "state": "failed",
        "uploaded_files": [
            {
                "path": "result.json",
                "size": result_path.stat().st_size,
                "sha256": __import__("hashlib").sha256(result_path.read_bytes()).hexdigest(),
                "uploaded_at": "2026-02-13T00:00:00+00:00",
                "file_id": "dummy_result",
            },
            {
                "path": "metrics.json",
                "size": metrics_path.stat().st_size,
                "sha256": __import__("hashlib").sha256(metrics_path.read_bytes()).hexdigest(),
                "uploaded_at": "2026-02-13T00:00:00+00:00",
                "file_id": "dummy_metrics",
            },
        ],
        "pending_files": [{"path": "scores.json"}],
        "failed_files": [{"path": "scores.json", "error": "upload failed"}],
        "retries": 1,
        "last_error": "upload failed",
        "dry_run": True,
        "manifest_committed_drive": False,
        "last_attempt_at": "2026-02-13T00:00:00+00:00",
    }
    _write(run_dir / "sync_state.json", json.dumps(previous_state))

    uploaded: list[str] = []

    def _fake_upload_with_retry(*, path: Path, **_kwargs):
        rel = path.relative_to(run_dir).as_posix()
        uploaded.append(rel)
        return {
            "path": rel,
            "size": path.stat().st_size,
            "sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
            "uploaded_at": "2026-02-13T00:01:00+00:00",
            "file_id": f"fake_{rel.replace('/', '_')}",
        }

    monkeypatch.setattr(
        "jarvis_core.ops_extract.drive_sync._upload_with_retry", _fake_upload_with_retry
    )

    state = sync_run_to_drive(
        run_dir=run_dir,
        enabled=True,
        dry_run=True,
        upload_workers=2,
    )

    assert uploaded == ["scores.json"]
    assert state["state"] == "committed"


def test_sync_sha_mismatch_detected(tmp_path: Path, monkeypatch):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    _setup_run_dir(run_dir)

    def _fake_upload_single_file(*, path: Path, run_dir: Path, **_kwargs):
        rel = path.relative_to(run_dir).as_posix()
        return {
            "path": rel,
            "size": path.stat().st_size,
            "sha256": "mismatch",
            "uploaded_at": "2026-02-13T00:01:00+00:00",
            "file_id": "fake",
        }

    monkeypatch.setattr(
        "jarvis_core.ops_extract.drive_sync._upload_single_file",
        _fake_upload_single_file,
    )

    state = sync_run_to_drive(
        run_dir=run_dir,
        enabled=True,
        dry_run=True,
        upload_workers=1,
        verify_sha256=True,
        max_retries=0,
    )

    assert state["state"] == "failed"
    assert "sha256" in state["last_error"]


def test_sync_retry_upper_bound(tmp_path: Path, monkeypatch):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    _setup_run_dir(run_dir)

    calls = {"count": 0}

    def _always_fail_upload(*_args, **_kwargs):
        calls["count"] += 1
        raise RuntimeError("forced_upload_failure")

    monkeypatch.setattr(
        "jarvis_core.ops_extract.drive_sync._upload_single_file",
        _always_fail_upload,
    )

    state = sync_run_to_drive(
        run_dir=run_dir,
        enabled=True,
        dry_run=True,
        upload_workers=1,
        max_retries=1,
        retry_backoff_sec=0.0,
    )

    assert state["state"] == "failed"
    assert calls["count"] >= 2
