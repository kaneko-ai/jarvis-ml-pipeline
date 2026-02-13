"""Metrics and warning builders for ops_extract mode."""

from __future__ import annotations

import re
from typing import Any


def build_text_quality_warnings(text: str) -> list[dict[str, Any]]:
    """Detect basic text quality issues for extraction audit."""
    warnings: list[dict[str, Any]] = []

    nul_count = text.count("\x00")
    if nul_count > 0:
        warnings.append(
            {
                "code": "TEXT_NUL_CHAR",
                "message": f"NUL characters detected: {nul_count}",
                "severity": "warning",
            }
        )

    control_chars = sum(1 for ch in text if ord(ch) < 32 and ch not in ("\n", "\r", "\t"))
    if control_chars > 0:
        warnings.append(
            {
                "code": "TEXT_CONTROL_CHAR",
                "message": f"Control characters detected: {control_chars}",
                "severity": "warning",
            }
        )

    multi_spaces = len(re.findall(r" {4,}", text))
    if multi_spaces > 0:
        warnings.append(
            {
                "code": "TEXT_MULTI_SPACE",
                "message": f"Long whitespace sequences detected: {multi_spaces}",
                "severity": "info",
            }
        )

    non_printable = sum(
        1 for ch in text if ch.isprintable() is False and ch not in ("\n", "\r", "\t")
    )
    ratio = (non_printable / max(len(text), 1)) * 100.0
    if ratio >= 1.0:
        warnings.append(
            {
                "code": "TEXT_NON_PRINTABLE_RATIO",
                "message": f"Non-printable character ratio is high: {ratio:.2f}%",
                "severity": "warning",
            }
        )

    return warnings


def build_metrics(
    *,
    run_duration_sec: float,
    text_source: str,
    total_chars: int,
    chars_per_page_mean: float,
    empty_page_ratio: float,
    encoding_warnings_count: int,
    figure_count: int = 0,
    table_count: int = 0,
    ocr_used: bool = False,
    needs_ocr_reason: str = "not_needed",
    retry_count: int = 0,
    resume_count: int = 0,
    sync_state: str = "not_started",
    manifest_committed_local: bool = True,
    manifest_committed_drive: bool = False,
    required_outputs_present: bool = True,
) -> dict[str, Any]:
    """Build metrics.json payload."""
    ops = {
        "run_duration_sec": round(float(run_duration_sec), 6),
        "resume_count": int(resume_count),
        "retry_count": int(retry_count),
        "sync_state": str(sync_state),
        "manifest_committed_local": bool(manifest_committed_local),
        "manifest_committed_drive": bool(manifest_committed_drive),
        "required_outputs_present": bool(required_outputs_present),
    }
    extract = {
        "text_source": str(text_source),
        "total_chars": int(total_chars),
        "chars_per_page_mean": float(chars_per_page_mean),
        "empty_page_ratio": float(empty_page_ratio),
        "encoding_warnings_count": int(encoding_warnings_count),
        "figure_count": int(figure_count),
        "table_count": int(table_count),
        "ocr_used": bool(ocr_used),
        "needs_ocr_reason": str(needs_ocr_reason),
    }
    return {
        "ops": ops,
        "extract": extract,
        "run_duration_sec": ops["run_duration_sec"],
        "sync_state": ops["sync_state"],
        "text_source": extract["text_source"],
        "ocr_used": extract["ocr_used"],
    }


def warning_messages(records: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("message", "")).strip() for item in records if item.get("message")]
