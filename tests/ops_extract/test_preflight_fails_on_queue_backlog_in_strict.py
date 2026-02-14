from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.preflight import run_preflight_checks


def test_preflight_fails_on_queue_backlog_in_strict(tmp_path: Path):
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")
    queue_dir = tmp_path / "sync_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(3):
        (queue_dir / f"item-{idx}.json").write_text(
            json.dumps(
                {
                    "schema_version": "ops_extract_contract_v2",
                    "run_id": f"r{idx}",
                    "state": "pending",
                    "created_at": "2025-01-01T00:00:00+00:00",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    report = run_preflight_checks(
        input_paths=[input_pdf],
        config=OpsExtractConfig(
            enabled=True,
            sync_enabled=True,
            sync_queue_dir=str(queue_dir),
            preflight_rule_mode="strict",
            lessons_path=str(tmp_path / "lessons.md"),
        ),
    )

    assert report.passed is False
    assert any("check_sync_queue_backlog" in error for error in report.errors)
