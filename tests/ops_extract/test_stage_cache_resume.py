from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jarvis_core.ingestion.robust_extractor import ExtractionResult
from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator


def _extraction(text: str) -> ExtractionResult:
    return ExtractionResult(
        text=text,
        pages=[(1, text)],
        method="pypdf",
        warnings=[],
        success=True,
    )


def test_stage_cache_skip_and_recompute(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    orchestrator = OpsExtractOrchestrator(
        run_dir=run_dir,
        config=OpsExtractConfig(
            enabled=True,
            resume_enabled=True,
            lessons_path=str(tmp_path / "lessons.md"),
        ),
    )

    with patch(
        "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
        return_value=_extraction("A" * 1200),
    ):
        outcome_first = orchestrator.run(run_id="resume-1", project="demo", input_paths=[pdf])
    assert outcome_first.status == "success"
    stage_cache_first = json.loads((run_dir / "stage_cache.json").read_text(encoding="utf-8"))
    assert stage_cache_first["stages"]["normalize_text"]["status"] == "computed"

    with patch(
        "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
        return_value=_extraction("A" * 1200),
    ):
        outcome_second = orchestrator.run(run_id="resume-1", project="demo", input_paths=[pdf])
    assert outcome_second.status == "success"
    assert not any(w.get("code") == "RECOMPUTED" for w in outcome_second.warning_records)
    stage_cache_second = json.loads((run_dir / "stage_cache.json").read_text(encoding="utf-8"))
    assert stage_cache_second["stages"]["normalize_text"]["status"] == "skipped"

    with patch(
        "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
        return_value=_extraction("B" * 1200),
    ):
        outcome_third = orchestrator.run(run_id="resume-1", project="demo", input_paths=[pdf])
    assert outcome_third.status == "success"
    assert any(w.get("code") == "RECOMPUTED" for w in outcome_third.warning_records)
    stage_cache_third = json.loads((run_dir / "stage_cache.json").read_text(encoding="utf-8"))
    assert stage_cache_third["stages"]["normalize_text"]["status"] == "computed"
