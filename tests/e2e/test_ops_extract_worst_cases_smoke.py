from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.doctor import run_doctor
from jarvis_core.ops_extract.drive_sync import sync_run_to_drive
from jarvis_core.ops_extract.schema_validate import validate_run_contracts_strict


def test_worst_case_contract_missing_smoke(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "ops_extract_contract_v2",
                "status": "success",
                "outputs": [{"path": "result.json", "size": 1, "sha256": "a" * 64}],
            }
        ),
        encoding="utf-8",
    )
    errors = validate_run_contracts_strict(run_dir, include_ocr_meta=False)
    assert any(error.startswith("missing:") for error in errors)


def test_worst_case_drive_sync_targets_manifest_outputs_smoke(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    out_dir = run_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "x.json").write_text("{}", encoding="utf-8")
    (out_dir / "y.json").write_text("{}", encoding="utf-8")
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "ops_extract_contract_v2",
                "run_id": "r1",
                "project": "demo",
                "created_at": "2026-02-14T00:00:00+00:00",
                "finished_at": "2026-02-14T00:00:00+00:00",
                "status": "success",
                "inputs": [],
                "outputs": [
                    {"path": "out/x.json", "size": 2, "sha256": "x" * 64},
                    {"path": "out/y.json", "size": 2, "sha256": "y" * 64},
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
            }
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
    assert {"out/x.json", "out/y.json", "manifest.json"}.issubset(uploaded_paths)


def test_worst_case_doctor_has_next_commands_smoke(tmp_path: Path):
    queue_dir = tmp_path / "sync_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    (queue_dir / "r1.json").write_text(
        json.dumps({"run_id": "r1", "state": "failed", "created_at": "2026-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    with patch(
        "jarvis_core.ops_extract.doctor.detect_network_profile",
        return_value=("OFFLINE", {"drive_api_reachable": False}),
    ):
        report = run_doctor(
            config=OpsExtractConfig(enabled=True, sync_queue_dir=str(queue_dir)),
            queue_dir=queue_dir,
            reports_dir=tmp_path / "doctor_reports",
        )
    content = report.read_text(encoding="utf-8")
    assert "## Next Commands" in content
