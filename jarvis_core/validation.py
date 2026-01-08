"""Validation helpers for self-evaluation flows.

This module intentionally keeps validation lightweight and dependency-free
so that execution and retry logic can reuse simple sanity checks.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis_core.validation")


@dataclass
class EvaluationResult:
    """Container for validation outcomes."""

    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] | None = field(default_factory=list)
    meta: dict[str, Any] | None = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []
        if self.meta is None:
            self.meta = {}


def _append_error(errors: list[str], message: str) -> None:
    errors.append(message)
    logger.info(message)


def validate_json_schema(data: Any, schema: dict[str, Any]) -> EvaluationResult:
    """Perform a lightweight structural validation against a simple schema.

    The schema is expected to be a mapping of key -> expected type (or tuple of
    types). Only presence and basic ``isinstance`` checks are performed to avoid
    external dependencies. Missing keys or type mismatches are recorded as
    errors.
    """

    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(schema, dict):
        _append_error(errors, "Schema must be a dictionary of key -> type")
        return EvaluationResult(ok=False, errors=errors, warnings=warnings)

    if not isinstance(data, dict):
        _append_error(errors, f"Data must be a dictionary; got {type(data).__name__}")
        return EvaluationResult(ok=False, errors=errors, warnings=warnings)

    for key, expected_type in schema.items():
        if key not in data:
            _append_error(errors, f"Missing key: {key}")
            continue

        value = data[key]
        expected: Iterable[type] | type
        if isinstance(expected_type, tuple):
            expected = expected_type
        else:
            expected = (expected_type,) if isinstance(expected_type, type) else (type(expected_type),)

        if not isinstance(value, tuple(expected)):
            _append_error(
                errors,
                f"Key '{key}' expected type {expected}; got {type(value).__name__}",
            )

    ok = len(errors) == 0
    if ok:
        logger.debug("Validation success for keys: %s", list(schema.keys()))
    return EvaluationResult(ok=ok, errors=errors, warnings=warnings)


def validate_file_exists(path: str) -> EvaluationResult:
    """Validate that a filesystem path exists."""

    errors: list[str] = []
    target = Path(path)
    if not target.exists():
        _append_error(errors, f"File does not exist: {path}")
    return EvaluationResult(ok=len(errors) == 0, errors=errors, warnings=[])


def combine_evaluations(*results: EvaluationResult) -> EvaluationResult:
    """Merge multiple evaluation results into a single aggregated outcome."""

    errors: list[str] = []
    warnings: list[str] = []
    meta: dict[str, Any] = {}

    for res in results:
        errors.extend(res.errors)
        if res.warnings:
            warnings.extend(res.warnings)
        if res.meta:
            meta.update(res.meta)

    ok = all(res.ok for res in results)
    return EvaluationResult(ok=ok, errors=errors, warnings=warnings, meta=meta)
