from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.ops_extract.drive_sync import sync_run_to_drive


def test_drive_sync_targets_manifest_outputs(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    first = run_dir / "artifacts" / "a.json"
    second = run_dir / "artifacts" / "b.json"
    first.write_text("{}", encoding="utf-8")
    second.write_text("{}", encoding="utf-8")
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "ops_extract_contract_v2",
                "run_id": "r1",
                "project": "demo",
                "created_at": "2026-02-14T00:00:00+00:00",
                "finished_at": "2026-02-14T00:00:01+00:00",
                "status": "success",
                "inputs": [],
                "outputs": [
                    {"path": "artifacts/a.json", "size": 2, "sha256": "a" * 64},
                    {"path": "artifacts/b.json", "size": 2, "sha256": "b" * 64},
                ],
                "extract": {
                    "method": "pdf_text",
                    "needs_ocr": False,
                    "needs_ocr_reason": "",
                    "total_chars": 2,
                    "chars_per_page_mean": 2.0,
                    "empty_page_ratio": 0.0,
                },
                "ops": {"retries": 0, "resume_count": 0, "sync_state": "not_started"},
                "committed": False,
                "committed_local": True,
                "committed_drive": False,
                "version": "ops_extract_manifest_v2",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    state = sync_run_to_drive(
        run_dir=run_dir,
        enabled=True,
        dry_run=True,
        upload_workers=2,
    )
    uploaded_paths = {str(item.get("path", "")).strip() for item in state["uploaded_files"]}
    assert "artifacts/a.json" in uploaded_paths
    assert "artifacts/b.json" in uploaded_paths
    assert "manifest.json" in uploaded_paths
