from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jarvis_core.ingestion.robust_extractor import ExtractionResult
from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator


def _stable_extraction() -> ExtractionResult:
    text = "Deterministic output " * 100
    return ExtractionResult(
        text=text,
        pages=[(1, text)],
        method="pypdf",
        warnings=[],
        success=True,
    )


def _manifest_output_hashes(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {item["path"]: item["sha256"] for item in payload.get("outputs", [])}


def test_manifest_output_hashes_are_deterministic(monkeypatch, tmp_path: Path):
    fixed_time = "2026-02-13T00:00:00+00:00"
    monkeypatch.setenv("JARVIS_OPS_EXTRACT_FIXED_TIME", fixed_time)

    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    lessons = tmp_path / "lessons.md"

    run_dir_a = tmp_path / "run-a"
    run_dir_b = tmp_path / "run-b"
    orchestrator_a = OpsExtractOrchestrator(
        run_dir=run_dir_a,
        config=OpsExtractConfig(enabled=True, lessons_path=str(lessons), resume_enabled=True),
    )
    orchestrator_b = OpsExtractOrchestrator(
        run_dir=run_dir_b,
        config=OpsExtractConfig(enabled=True, lessons_path=str(lessons), resume_enabled=True),
    )

    with patch(
        "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
        return_value=_stable_extraction(),
    ):
        result_a = orchestrator_a.run(run_id="deterministic", project="demo", input_paths=[pdf])
        result_b = orchestrator_b.run(run_id="deterministic", project="demo", input_paths=[pdf])

    assert result_a.status == "success"
    assert result_b.status == "success"
    hashes_a = _manifest_output_hashes(run_dir_a / "manifest.json")
    hashes_b = _manifest_output_hashes(run_dir_b / "manifest.json")
    assert hashes_a == hashes_b
