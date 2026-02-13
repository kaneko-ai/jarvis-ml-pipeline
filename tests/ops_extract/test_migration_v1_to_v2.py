from __future__ import annotations

import json
from pathlib import Path

from scripts.migrate_ops_extract_runs_v1_to_v2 import migrate_run


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_migration_v1_to_v2_adds_required_files_and_keys(tmp_path: Path):
    run_dir = tmp_path / "runs" / "r1"
    run_dir.mkdir(parents=True)
    _write_json(run_dir / "manifest.json", {"run_id": "r1", "committed": True})
    _write_json(
        run_dir / "sync_state.json",
        {
            "version": "ops_extract_sync_v1",
            "state": "failed",
            "uploaded_files": [{"path": "result.json", "size": 1, "sha256": "abc"}],
            "pending_files": [],
            "failed_files": [],
            "retries": 0,
            "resume_count": 0,
            "last_error": "",
            "dry_run": True,
            "manifest_committed_drive": False,
            "last_attempt_at": "2026-02-13T00:00:00+00:00",
        },
    )

    changed = migrate_run(run_dir, dry_run=False)
    assert changed is True

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "ops_extract_contract_v2"
    assert manifest["committed_local"] is True
    assert manifest["committed_drive"] is False

    sync_state = json.loads((run_dir / "sync_state.json").read_text(encoding="utf-8"))
    assert sync_state["version"] == "ops_extract_sync_v2"
    assert sync_state["schema_version"] == "ops_extract_contract_v2"
    assert "verified" in sync_state["uploaded_files"][0]
    assert "attempts" in sync_state["uploaded_files"][0]

    assert (run_dir / "stage_cache.json").exists()
    assert (run_dir / "trace.jsonl").exists()
    assert (run_dir / "ingestion" / "pdf_diagnosis.json").exists()
