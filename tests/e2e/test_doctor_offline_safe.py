from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.doctor import run_doctor


def test_doctor_offline_safe(tmp_path: Path):
    queue_dir = tmp_path / "sync_queue"
    queue_dir.mkdir(parents=True)
    (queue_dir / "r1.json").write_text(
        json.dumps({"run_id": "r1", "state": "failed", "last_error": "network"}),
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
    assert report.exists()
    content = report.read_text(encoding="utf-8")
    assert "network_profile: OFFLINE" in content
