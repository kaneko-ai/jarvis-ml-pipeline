from pathlib import Path
from unittest.mock import patch

from jarvis_core.ingestion.robust_extractor import ExtractionResult
from jarvis_core.ops_extract.contracts import OpsExtractConfig, OpsExtractThresholds
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator


def _good_extraction() -> ExtractionResult:
    return ExtractionResult(
        text="A" * 1400,
        pages=[(1, "A" * 700), (2, "A" * 700)],
        method="pypdf",
        warnings=[],
        success=True,
    )


def _low_extraction() -> ExtractionResult:
    return ExtractionResult(
        text="short",
        pages=[(1, "")],
        method="pypdf",
        warnings=[{"category": "parser", "message": "parse failed"}],
        success=True,
    )


def test_orchestrator_success_non_ocr(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    orchestrator = OpsExtractOrchestrator(
        run_dir,
        OpsExtractConfig(enabled=True, lessons_path=str(tmp_path / "lessons.md")),
    )
    with patch(
        "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
        return_value=_good_extraction(),
    ):
        outcome = orchestrator.run(run_id="r1", project="p1", input_paths=[pdf])

    assert outcome.status == "success"
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "ingestion" / "text.md").exists()
    assert outcome.text_source in {"pdf_text", "mixed"}


def test_orchestrator_fails_when_ocr_required_but_yomitoku_missing(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    cfg = OpsExtractConfig(
        enabled=True,
        lessons_path=str(tmp_path / "lessons.md"),
        thresholds=OpsExtractThresholds(
            min_total_chars=800, min_chars_per_page=200, empty_page_ratio_threshold=0.6
        ),
    )
    orchestrator = OpsExtractOrchestrator(run_dir, cfg)

    with (
        patch(
            "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
            return_value=_low_extraction(),
        ),
        patch("jarvis_core.ops_extract.orchestrator.check_yomitoku_available", return_value=False),
    ):
        outcome = orchestrator.run(run_id="r2", project="p1", input_paths=[pdf])

    assert outcome.status == "failed"
    assert (run_dir / "failure_analysis.json").exists()
    assert (run_dir / "manifest.json").exists()
    assert outcome.manifest["status"] == "failed"


def test_orchestrator_ocr_path_success(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdf = tmp_path / "scan2.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    cfg = OpsExtractConfig(enabled=True, lessons_path=str(tmp_path / "lessons.md"))
    orchestrator = OpsExtractOrchestrator(run_dir, cfg)

    with (
        patch(
            "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
            return_value=_low_extraction(),
        ),
        patch("jarvis_core.ops_extract.orchestrator.check_yomitoku_available", return_value=True),
        patch(
            "jarvis_core.ops_extract.orchestrator.rasterize_pdf_to_images",
            return_value={
                "page_count": 1,
                "image_paths": [str(tmp_path / "page_0001.png")],
                "dpi": 300,
                "generated_at": "2026-02-13T00:00:00+00:00",
            },
        ),
        patch(
            "jarvis_core.ops_extract.orchestrator.run_yomitoku_cli",
            return_value={
                "text": "OCR extracted content",
                "text_path": str(tmp_path / "ocr_result.md"),
                "returncode": 0,
                "figure_count": 1,
            },
        ),
    ):
        outcome = orchestrator.run(run_id="r3", project="p1", input_paths=[pdf])

    assert outcome.status == "success"
    assert outcome.ocr_used is True
    assert (run_dir / "ocr" / "ocr_meta.json").exists()


def test_orchestrator_sync_failure_records_warning_and_sync_state(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    cfg = OpsExtractConfig(
        enabled=True,
        lessons_path=str(tmp_path / "lessons.md"),
        sync_enabled=True,
        sync_dry_run=True,
    )
    orchestrator = OpsExtractOrchestrator(run_dir, cfg)

    with (
        patch(
            "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
            return_value=_good_extraction(),
        ),
        patch(
            "jarvis_core.ops_extract.orchestrator.sync_run_to_drive",
            return_value={
                "state": "failed",
                "manifest_committed_drive": False,
                "retries": 2,
                "resume_count": 1,
                "last_error": "forced sync failure",
            },
        ),
    ):
        outcome = orchestrator.run(run_id="r-sync-fail", project="p1", input_paths=[pdf])

    assert outcome.metrics["ops"]["sync_state"] == "failed"
    assert outcome.metrics["ops"]["retry_count"] == 2
    assert outcome.metrics["ops"]["resume_count"] == 1
    assert any("forced sync failure" in msg for msg in outcome.warning_messages)
