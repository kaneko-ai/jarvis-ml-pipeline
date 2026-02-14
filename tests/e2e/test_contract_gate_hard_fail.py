from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jarvis_core.ingestion.robust_extractor import ExtractionResult
from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator


def _good_extraction() -> ExtractionResult:
    text = "A" * 1600
    return ExtractionResult(
        text=text,
        pages=[(1, text)],
        method="pypdf",
        warnings=[],
        success=True,
    )


def test_contract_validation_forces_failed_status(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdf = tmp_path / "input.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    orchestrator = OpsExtractOrchestrator(
        run_dir=run_dir,
        config=OpsExtractConfig(enabled=True, lessons_path=str(tmp_path / "lessons.md")),
    )

    with (
        patch(
            "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
            return_value=_good_extraction(),
        ),
        patch(
            "jarvis_core.ops_extract.orchestrator.validate_run_contracts",
            return_value=["manifest.schema.json:required status"],
        ),
    ):
        outcome = orchestrator.run(run_id="contract-fail", project="demo", input_paths=[pdf])

    assert outcome.status == "failed"
    failure_analysis = json.loads((run_dir / "failure_analysis.json").read_text(encoding="utf-8"))
    assert failure_analysis["category"] == "contract_violation"
    warnings = json.loads((run_dir / "warnings.json").read_text(encoding="utf-8"))["warnings"]
    assert any(w.get("code") == "CONTRACT_VALIDATION_FAILED" for w in warnings)
    assert (run_dir / "crash_dump.json").exists()

