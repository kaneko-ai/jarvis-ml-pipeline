from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator


def test_crash_dump_written_on_failure(tmp_path: Path):
    run_dir = tmp_path / "run"
    missing_pdf = tmp_path / "missing.pdf"
    orchestrator = OpsExtractOrchestrator(
        run_dir=run_dir,
        config=OpsExtractConfig(enabled=True, lessons_path=str(tmp_path / "lessons.md")),
    )

    outcome = orchestrator.run(run_id="crash-1", project="demo", input_paths=[missing_pdf])
    assert outcome.status == "failed"

    crash_dump_path = run_dir / "crash_dump.json"
    assert crash_dump_path.exists()
    payload = json.loads(crash_dump_path.read_text(encoding="utf-8"))
    assert payload["error"]
    assert "environment" in payload
    assert "os" in payload["environment"]
    assert "python" in payload["environment"]
    assert "disk" in payload["environment"]
    assert "gpu" in payload["environment"]
