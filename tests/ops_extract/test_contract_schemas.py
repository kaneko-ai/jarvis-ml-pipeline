from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from jarvis_core.ingestion.robust_extractor import ExtractionResult
from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.orchestrator import OpsExtractOrchestrator
from jarvis_core.ops_extract.schema_validate import (
    SchemaValidationError,
    validate_contract_path,
    validate_run_contracts,
)


def _good_extraction() -> ExtractionResult:
    return ExtractionResult(
        text="A" * 1200,
        pages=[(1, "A" * 600), (2, "A" * 600)],
        method="pypdf",
        warnings=[],
        success=True,
    )


def test_contract_schemas_pass_on_generated_run(tmp_path: Path):
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
        outcome = orchestrator.run(run_id="schema-run", project="demo", input_paths=[pdf])

    assert outcome.status == "success"
    errors = validate_run_contracts(run_dir)
    assert errors == []


def test_contract_schema_fails_when_required_key_missing(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": "r1",
                "project": "p1",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SchemaValidationError):
        validate_contract_path(manifest_path, contract_name="manifest.json")


def test_trace_schema_fails_on_invalid_payload(tmp_path: Path):
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text(
        json.dumps(
            {
                "schema_version": "ops_extract_contract_v2",
                "stage_id": "preflight",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(SchemaValidationError):
        validate_contract_path(trace_path, contract_name="trace.jsonl")
