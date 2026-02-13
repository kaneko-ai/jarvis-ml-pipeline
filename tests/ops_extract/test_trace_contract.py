from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jarvis_core.ingestion.robust_extractor import ExtractionResult
from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator, STAGE_IDS


def _good_extraction() -> ExtractionResult:
    return ExtractionResult(
        text="A" * 1200,
        pages=[(1, "A" * 600), (2, "A" * 600)],
        method="pypdf",
        warnings=[],
        success=True,
    )


def _read_trace(path: Path) -> list[dict]:
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def test_trace_contract_contains_all_stages(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdf = tmp_path / "input.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    orchestrator = OpsExtractOrchestrator(
        run_dir=run_dir,
        config=OpsExtractConfig(enabled=True, lessons_path=str(tmp_path / "lessons.md")),
    )

    with patch(
        "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
        return_value=_good_extraction(),
    ):
        outcome = orchestrator.run(run_id="trace-ok", project="demo", input_paths=[pdf])

    assert outcome.status == "success"
    trace_rows = _read_trace(run_dir / "trace.jsonl")
    assert [row["stage_id"] for row in trace_rows] == STAGE_IDS
    for row in trace_rows:
        assert "start_ts" in row
        assert "end_ts" in row
        assert "duration" in row
        assert "inputs" in row
        assert "outputs" in row
        assert "retry_count" in row
        assert "error" in row


def test_trace_contract_records_error_stage(tmp_path: Path):
    run_dir = tmp_path / "run"
    missing_pdf = tmp_path / "missing.pdf"
    orchestrator = OpsExtractOrchestrator(
        run_dir=run_dir,
        config=OpsExtractConfig(enabled=True, lessons_path=str(tmp_path / "lessons.md")),
    )

    outcome = orchestrator.run(run_id="trace-fail", project="demo", input_paths=[missing_pdf])
    assert outcome.status == "failed"
    trace_rows = _read_trace(run_dir / "trace.jsonl")
    discover = [row for row in trace_rows if row["stage_id"] == "discover_inputs"][0]
    assert discover["error"] is not None
