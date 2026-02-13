from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

from jarvis_core.ingestion.robust_extractor import ExtractionResult
from jarvis_core.ops_extract.contracts import OpsExtractConfig, OpsExtractThresholds
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator


def _mk_pdf(path: Path) -> None:
    path.write_bytes(b"%PDF-1.4")


def test_parallel_pipeline_preserves_input_order(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdfs = [tmp_path / f"doc{i}.pdf" for i in [1, 2, 3]]
    for pdf in pdfs:
        _mk_pdf(pdf)

    delays = {"doc1.pdf": 0.03, "doc2.pdf": 0.01, "doc3.pdf": 0.0}

    def _fake_extract(_self, filepath: Path):
        time.sleep(delays[filepath.name])
        text = f"CONTENT_{filepath.stem}" * 150
        return ExtractionResult(
            text=text,
            pages=[(1, text)],
            method="pypdf",
            warnings=[],
            success=True,
        )

    orchestrator = OpsExtractOrchestrator(
        run_dir,
        OpsExtractConfig(enabled=True, parse_workers=3, lessons_path=str(tmp_path / "lessons.md")),
    )

    with patch("jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract", _fake_extract):
        outcome = orchestrator.run(run_id="r-order", project="p1", input_paths=pdfs)

    assert outcome.status == "success"
    text_md = (run_dir / "ingestion" / "text.md").read_text(encoding="utf-8")
    pos1 = text_md.find("## doc1.pdf")
    pos2 = text_md.find("## doc2.pdf")
    pos3 = text_md.find("## doc3.pdf")
    assert pos1 < pos2 < pos3


def test_parallel_pipeline_partial_failure_keeps_contract(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdfs = [tmp_path / "ok.pdf", tmp_path / "fail.pdf"]
    for pdf in pdfs:
        _mk_pdf(pdf)

    def _fake_extract(_self, filepath: Path):
        if filepath.name == "fail.pdf":
            raise RuntimeError("forced_parse_failure")
        text = "A" * 1600
        return ExtractionResult(
            text=text,
            pages=[(1, text)],
            method="pypdf",
            warnings=[],
            success=True,
        )

    orchestrator = OpsExtractOrchestrator(
        run_dir,
        OpsExtractConfig(enabled=True, parse_workers=2, lessons_path=str(tmp_path / "lessons.md")),
    )

    with patch("jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract", _fake_extract):
        outcome = orchestrator.run(run_id="r-fail", project="p1", input_paths=pdfs)

    assert outcome.status == "failed"
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "failure_analysis.json").exists()
    assert (run_dir / "warnings.jsonl").exists()


def test_parallel_pipeline_parallel_ocr_stage(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdfs = [tmp_path / "scan1.pdf", tmp_path / "scan2.pdf"]
    for pdf in pdfs:
        _mk_pdf(pdf)

    def _low_extract(_self, _filepath: Path):
        return ExtractionResult(
            text="short",
            pages=[(1, "")],
            method="pypdf",
            warnings=[{"category": "parser", "message": "low text"}],
            success=True,
        )

    ocr_called: list[str] = []

    def _fake_yomi(*, input_path: Path, **_kwargs):
        ocr_called.append(input_path.name)
        return {
            "text": f"OCR_{input_path.stem}" * 40,
            "text_path": str(tmp_path / f"{input_path.stem}.md"),
            "returncode": 0,
            "figure_count": 1,
        }

    orchestrator = OpsExtractOrchestrator(
        run_dir,
        OpsExtractConfig(
            enabled=True,
            parse_workers=2,
            ocr_workers=2,
            lessons_path=str(tmp_path / "lessons.md"),
            thresholds=OpsExtractThresholds(
                min_total_chars=800,
                min_chars_per_page=200,
                empty_page_ratio_threshold=0.6,
            ),
        ),
    )

    with (
        patch("jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract", _low_extract),
        patch("jarvis_core.ops_extract.orchestrator.check_yomitoku_available", return_value=True),
        patch(
            "jarvis_core.ops_extract.orchestrator.rasterize_pdf_to_images",
            return_value={"page_count": 1, "image_paths": [], "dpi": 300},
        ),
        patch("jarvis_core.ops_extract.orchestrator.run_yomitoku_cli", side_effect=_fake_yomi),
    ):
        outcome = orchestrator.run(run_id="r-ocr", project="p1", input_paths=pdfs)

    assert outcome.status == "success"
    assert outcome.ocr_used is True
    assert sorted(ocr_called) == ["scan1.pdf", "scan2.pdf"]
