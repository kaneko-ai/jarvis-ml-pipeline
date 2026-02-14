from __future__ import annotations

import pytest

from jarvis_core.ops_extract.schema_validate import SchemaValidationError, validate_payload


def test_schema_validate_smoke_minimal_payloads():
    validate_payload(
        {
            "schema_version": "ops_extract_contract_v2",
            "run_id": "r1",
            "project": "demo",
            "created_at": "2026-02-14T00:00:00+00:00",
            "finished_at": "2026-02-14T00:00:00+00:00",
            "status": "success",
            "inputs": [],
            "outputs": [],
            "extract": {
                "method": "pdf_text",
                "needs_ocr": False,
                "needs_ocr_reason": "not_needed",
                "total_chars": 0,
                "chars_per_page_mean": 0.0,
                "empty_page_ratio": 0.0,
            },
            "ops": {"retries": 0, "resume_count": 0, "sync_state": "not_started"},
            "committed": True,
            "committed_local": True,
            "committed_drive": False,
            "version": "ops_extract_v1",
        },
        schema_file="manifest.schema.json",
    )
    validate_payload(
        {
            "schema_version": "ops_extract_contract_v2",
            "run_id": "r1",
            "project": "demo",
            "source": "pdf_text",
            "entries": [],
        },
        schema_file="text_source.schema.json",
    )
    validate_payload(
        {
            "schema_version": "ops_extract_contract_v2",
            "generated_at": "2026-02-14T00:00:00+00:00",
            "profile": "ONLINE",
            "diagnosis": {"drive_api_reachable": True},
        },
        schema_file="network_diagnosis.schema.json",
    )


def test_schema_validate_fails_without_schema_version():
    with pytest.raises(SchemaValidationError):
        validate_payload(
            {
                "run_id": "r1",
                "project": "demo",
                "source": "pdf_text",
                "entries": [],
            },
            schema_file="text_source.schema.json",
        )
