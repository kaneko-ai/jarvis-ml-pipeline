from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.doctor import run_doctor


def test_doctor_includes_next_commands(tmp_path: Path):
    queue_dir = tmp_path / "sync_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    (queue_dir / "r1.json").write_text(
        json.dumps(
            {
                "schema_version": "ops_extract_contract_v2",
                "run_id": "r1",
                "state": "human_action_required",
                "created_at": "2026-02-01T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    with patch(
        "jarvis_core.ops_extract.doctor.detect_network_profile",
        return_value=("ONLINE", {"drive_api_reachable": True}),
    ):
        report = run_doctor(
            config=OpsExtractConfig(enabled=True, sync_queue_dir=str(queue_dir)),
            queue_dir=queue_dir,
            reports_dir=tmp_path / "doctor_reports",
        )
    content = report.read_text(encoding="utf-8")
    assert "## Next Commands" in content
    assert "javisctl sync --only-human-action" in content
