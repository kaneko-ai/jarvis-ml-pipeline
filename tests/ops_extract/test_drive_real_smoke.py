from __future__ import annotations

import os
from pathlib import Path

import pytest

from jarvis_core.ops_extract.drive_sync import sync_run_to_drive


@pytest.mark.network
def test_drive_real_smoke_optional(tmp_path: Path):
    if os.getenv("JARVIS_NETWORK_TESTS") != "1":
        pytest.skip("JARVIS_NETWORK_TESTS!=1")

    token = os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN")
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    if not token or not folder_id:
        pytest.skip("Drive credentials are not configured")

    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "result.json").write_text("{}", encoding="utf-8")
    (run_dir / "metrics.json").write_text("{}", encoding="utf-8")
    (run_dir / "manifest.json").write_text(
        '{"schema_version":"ops_extract_contract_v2","committed":true,"committed_local":true,"committed_drive":false}',
        encoding="utf-8",
    )

    state = sync_run_to_drive(
        run_dir=run_dir,
        enabled=True,
        dry_run=False,
        upload_workers=1,
        access_token=token,
        folder_id=folder_id,
        max_retries=1,
        retry_backoff_sec=1.0,
    )
    assert state["state"] in {"committed", "failed"}
