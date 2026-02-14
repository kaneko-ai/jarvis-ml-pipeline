"""JSON Schema validators for ops_extract contract artifacts."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .contracts import OPS_EXTRACT_SCHEMA_VERSION

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "ops_extract"

SCHEMA_BY_FILENAME = {
    "manifest.json": "manifest.schema.json",
    "metrics.json": "metrics.schema.json",
    "warnings.json": "warnings.schema.json",
    "failure_analysis.json": "failure_analysis.schema.json",
    "run_metadata.json": "run_metadata.schema.json",
    "sync_state.json": "sync_state.schema.json",
    "trace.jsonl": "trace.schema.json",
    "stage_cache.json": "stage_cache.schema.json",
    "network_diagnosis.json": "network_diagnosis.schema.json",
    "crash_dump.json": "crash_dump.schema.json",
    "ingestion/pdf_diagnosis.json": "pdf_diagnosis.schema.json",
    "ingestion/text_source.json": "text_source.schema.json",
    "ocr/ocr_meta.json": "ocr_meta.schema.json",
}


class SchemaValidationError(ValueError):
    """Raised when a payload does not satisfy an ops_extract JSON Schema."""


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=32)
def _load_schema(schema_file: str) -> dict[str, Any]:
    path = SCHEMA_DIR / schema_file
    if not path.exists():
        raise FileNotFoundError(f"schema_not_found:{path}")
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"invalid_schema_payload:{path}")
    return payload


@lru_cache(maxsize=1)
def _validator() -> Any:
    try:
        import jsonschema
    except Exception as exc:  # pragma: no cover - import guard
        raise RuntimeError(
            "jsonschema package is required for ops_extract contract validation"
        ) from exc
    return jsonschema


def validate_payload(payload: Any, *, schema_file: str) -> None:
    schema = _load_schema(schema_file)
    jsonschema = _validator()
    try:
        jsonschema.validate(instance=payload, schema=schema)
    except Exception as exc:
        raise SchemaValidationError(f"schema_validation_failed:{schema_file}:{exc}") from exc


def schema_file_for_contract(contract_name: str) -> str:
    key = contract_name.replace("\\", "/")
    if key not in SCHEMA_BY_FILENAME:
        raise KeyError(f"unknown_contract:{contract_name}")
    return SCHEMA_BY_FILENAME[key]


def validate_contract_path(path: Path, *, contract_name: str | None = None) -> None:
    contract_name = contract_name or path.name
    schema_file = schema_file_for_contract(contract_name)
    if contract_name.endswith(".jsonl"):
        with open(path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                raw = line.strip()
                if not raw:
                    continue
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise SchemaValidationError(f"invalid_jsonl:{path}:{line_no}:{exc}") from exc
                if isinstance(payload, dict) and "schema_version" not in payload:
                    payload["schema_version"] = OPS_EXTRACT_SCHEMA_VERSION
                validate_payload(payload, schema_file=schema_file)
        return

    payload = _load_json(path)
    validate_payload(payload, schema_file=schema_file)


def validate_run_contracts(run_dir: Path) -> list[str]:
    """Validate all known contract files under a run directory.

    Returns a list of validation error messages. Empty means success.
    """

    errors: list[str] = []
    for filename in SCHEMA_BY_FILENAME:
        path = run_dir / filename
        if not path.exists():
            continue
        try:
            validate_contract_path(path, contract_name=filename)
        except Exception as exc:
            errors.append(str(exc))
    return errors


def list_expected_contract_files(*, include_ocr_meta: bool) -> list[str]:
    expected = []
    for filename in SCHEMA_BY_FILENAME:
        if filename == "crash_dump.json":
            continue
        if not include_ocr_meta and filename == "ocr/ocr_meta.json":
            continue
        expected.append(filename)
    return expected


def _read_run_status(run_dir: Path) -> str:
    run_metadata_path = run_dir / "run_metadata.json"
    manifest_path = run_dir / "manifest.json"
    for path in (run_metadata_path, manifest_path):
        if not path.exists():
            continue
        try:
            payload = _load_json(path)
        except Exception:
            continue
        if isinstance(payload, dict):
            status = str(payload.get("status", "")).strip().lower()
            if status:
                return status
    return ""


def _count_non_empty_jsonl_lines(path: Path) -> int:
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def validate_run_contracts_strict(run_dir: Path, *, include_ocr_meta: bool) -> list[str]:
    errors: list[str] = []

    expected = list_expected_contract_files(include_ocr_meta=include_ocr_meta)
    status = _read_run_status(run_dir)
    if status == "failed":
        expected.append("crash_dump.json")

    for filename in expected:
        path = run_dir / filename
        if not path.exists():
            errors.append(f"missing:{filename}")

    for filename in expected:
        path = run_dir / filename
        if not path.exists():
            continue
        try:
            validate_contract_path(path, contract_name=filename)
        except Exception as exc:
            errors.append(str(exc))

    trace_path = run_dir / "trace.jsonl"
    if trace_path.exists():
        try:
            if _count_non_empty_jsonl_lines(trace_path) == 0:
                errors.append("empty_jsonl:trace.jsonl")
        except Exception as exc:
            errors.append(f"jsonl_check_failed:trace.jsonl:{exc}")

    warnings_jsonl_path = run_dir / "warnings.jsonl"
    if warnings_jsonl_path.exists():
        try:
            if _count_non_empty_jsonl_lines(warnings_jsonl_path) == 0:
                errors.append("empty_jsonl:warnings.jsonl")
        except Exception as exc:
            errors.append(f"jsonl_check_failed:warnings.jsonl:{exc}")

    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        try:
            manifest_payload = _load_json(manifest_path)
            if isinstance(manifest_payload, dict):
                outputs = manifest_payload.get("outputs")
                if isinstance(outputs, list) and len(outputs) == 0:
                    errors.append("empty_outputs:manifest.json")
        except Exception as exc:
            errors.append(f"manifest_parse_failed:{exc}")

    return errors
