from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.ops_extract.telemetry.eta import ETAEstimator
from jarvis_core.ops_extract.telemetry.progress import ProgressEmitter


def test_progress_emitter_writes_jsonl(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    emitter = ProgressEmitter(run_dir, eta_estimator=ETAEstimator(tmp_path))
    emitter.emit_stage_start("extract_text_pdf", items_total=3)
    emitter.emit_stage_update("extract_text_pdf", 1, 3)
    emitter.emit_stage_end("extract_text_pdf")

    path = run_dir / "progress.jsonl"
    assert path.exists()
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert len(rows) >= 1
    assert all("overall_progress_percent" in row for row in rows)
