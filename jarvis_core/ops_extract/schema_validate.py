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
    if contract_name not in SCHEMA_BY_FILENAME:
        raise KeyError(f"unknown_contract:{contract_name}")
    return SCHEMA_BY_FILENAME[contract_name]


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
