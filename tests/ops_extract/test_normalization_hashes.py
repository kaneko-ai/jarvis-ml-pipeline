from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jarvis_core.ingestion.robust_extractor import ExtractionResult
from jarvis_core.ops_extract.contracts import OpsExtractConfig, OpsExtractThresholds
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator


def _raw_extraction() -> ExtractionResult:
    raw = "A    B\n\nC"
    return ExtractionResult(
        text=raw,
        pages=[(1, raw)],
        method="pypdf",
        warnings=[],
        success=True,
    )


def test_metrics_contains_raw_and_normalized_hashes(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    orchestrator = OpsExtractOrchestrator(
        run_dir,
        OpsExtractConfig(
            enabled=True,
            lessons_path=str(tmp_path / "lessons.md"),
            thresholds=OpsExtractThresholds(
                min_total_chars=1,
                min_chars_per_page=1,
                empty_page_ratio_threshold=1.0,
            ),
        ),
    )
    with patch(
        "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
        return_value=_raw_extraction(),
    ):
        outcome = orchestrator.run(run_id="norm-hash", project="demo", input_paths=[pdf])

    assert outcome.status == "success"
    raw_hash = outcome.metrics["extract"]["raw_text_sha256"]
    norm_hash = outcome.metrics["extract"]["normalized_text_sha256"]
    assert isinstance(raw_hash, str) and raw_hash
    assert isinstance(norm_hash, str) and norm_hash
    assert raw_hash != norm_hash
