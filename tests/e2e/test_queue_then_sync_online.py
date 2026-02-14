from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jarvis_core.ingestion.robust_extractor import ExtractionResult
from jarvis_core.ops_extract.cli import javisctl
from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator


def _good_extraction() -> ExtractionResult:
    text = "A" * 1200
    return ExtractionResult(
        text=text,
        pages=[(1, text)],
        method="pypdf",
        warnings=[],
        success=True,
    )


def test_queue_then_sync_online(monkeypatch, tmp_path: Path):
    run_dir = tmp_path / "run"
    queue_dir = tmp_path / "sync_queue"
    pdf = tmp_path / "input.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    orchestrator = OpsExtractOrchestrator(
        run_dir=run_dir,
        config=OpsExtractConfig(
            enabled=True,
            lessons_path=str(tmp_path / "lessons.md"),
            sync_enabled=True,
            sync_dry_run=False,
            sync_queue_dir=str(queue_dir),
            network_offline_policy="defer",
        ),
    )
    with (
        patch(
            "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
            return_value=_good_extraction(),
        ),
        patch(
            "jarvis_core.ops_extract.preflight.detect_network_profile",
            return_value=("OFFLINE", {"profile": "OFFLINE", "drive_api_reachable": False}),
        ),
    ):
        outcome = orchestrator.run(run_id="queue-sync", project="demo", input_paths=[pdf])
    assert outcome.status == "success"
    queue_item = queue_dir / "queue-sync.json"
    assert queue_item.exists()

    monkeypatch.setattr(
        "sys.argv",
        ["javisctl", "sync", "--queue-dir", str(queue_dir), "--dry-run"],
    )
    assert javisctl.main() == 0
    payload = json.loads(queue_item.read_text(encoding="utf-8"))
    assert payload["state"] == "done"

