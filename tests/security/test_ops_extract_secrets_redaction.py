from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jarvis_core.ingestion.robust_extractor import ExtractionResult
from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator
from jarvis_core.ops_extract.security import redact_sensitive_text


def _good_extraction() -> ExtractionResult:
    text = "A" * 1200
    return ExtractionResult(
        text=text,
        pages=[(1, text)],
        method="pypdf",
        warnings=[],
        success=True,
    )


def test_redact_sensitive_text_masks_bearer_and_tokens():
    message = "Authorization: Bearer abc123 token=xyz789"
    redacted = redact_sensitive_text(message)
    assert "abc123" not in redacted
    assert "xyz789" not in redacted


def test_ops_extract_run_metadata_masks_drive_token(tmp_path: Path):
    run_dir = tmp_path / "run"
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    orchestrator = OpsExtractOrchestrator(
        run_dir=run_dir,
        config=OpsExtractConfig(
            enabled=True,
            lessons_path=str(tmp_path / "lessons.md"),
            drive_access_token="super-secret-token",
        ),
    )
    with patch(
        "jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract",
        return_value=_good_extraction(),
    ):
        outcome = orchestrator.run(run_id="redact", project="demo", input_paths=[pdf])
    assert outcome.status == "success"
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["config"]["drive_access_token"] == "***redacted***"
