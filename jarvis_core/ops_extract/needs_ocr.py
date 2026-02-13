"""Rule-based OCR necessity decision."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import OpsExtractThresholds


@dataclass(frozen=True)
class NeedsOcrDecision:
    needs_ocr: bool
    reason: str
    metrics: dict[str, float | int]


def _has_parser_exception(exceptions_in_text_extract: list[Any] | None) -> bool:
    if not exceptions_in_text_extract:
        return False
    for item in exceptions_in_text_extract:
        if isinstance(item, dict):
            category = str(item.get("category", "")).lower()
            code = str(item.get("code", "")).lower()
            message = str(item.get("message", "")).lower()
            if "parser" in category or "parser" in code or "pdf" in message:
                return True
        else:
            if "parser" in str(item).lower():
                return True
    return False


def summarize_page_metrics(pages: list[tuple[int, str]] | None) -> dict[str, float | int]:
    """Summarize non-OCR extraction page quality indicators."""
    pages = pages or []
    page_count = len(pages)
    if page_count == 0:
        return {
            "total_chars_extracted": 0,
            "chars_per_page_mean": 0.0,
            "empty_page_ratio": 1.0,
            "page_count": 0,
            "empty_pages": 0,
        }

    lengths = [len((text or "").strip()) for _, text in pages]
    total_chars = sum(lengths)
    empty_pages = sum(1 for x in lengths if x == 0)

    return {
        "total_chars_extracted": total_chars,
        "chars_per_page_mean": total_chars / page_count if page_count else 0.0,
        "empty_page_ratio": empty_pages / page_count if page_count else 1.0,
        "page_count": page_count,
        "empty_pages": empty_pages,
    }


def decide_needs_ocr(
    *,
    total_chars_extracted: int,
    chars_per_page_mean: float,
    empty_page_ratio: float,
    exceptions_in_text_extract: list[Any] | None = None,
    thresholds: OpsExtractThresholds | None = None,
) -> NeedsOcrDecision:
    """Apply threshold-based OCR decision rules."""
    thresholds = thresholds or OpsExtractThresholds()
    parser_exception = _has_parser_exception(exceptions_in_text_extract)

    if total_chars_extracted < thresholds.min_total_chars:
        return NeedsOcrDecision(
            needs_ocr=True,
            reason="total_chars_below_threshold",
            metrics={
                "total_chars_extracted": total_chars_extracted,
                "chars_per_page_mean": chars_per_page_mean,
                "empty_page_ratio": empty_page_ratio,
                "parser_exception": int(parser_exception),
            },
        )

    if (
        chars_per_page_mean < thresholds.min_chars_per_page
        and empty_page_ratio > thresholds.empty_page_ratio_threshold
    ):
        return NeedsOcrDecision(
            needs_ocr=True,
            reason="low_chars_and_high_empty_pages",
            metrics={
                "total_chars_extracted": total_chars_extracted,
                "chars_per_page_mean": chars_per_page_mean,
                "empty_page_ratio": empty_page_ratio,
                "parser_exception": int(parser_exception),
            },
        )

    if parser_exception:
        return NeedsOcrDecision(
            needs_ocr=True,
            reason="parser_exception_detected",
            metrics={
                "total_chars_extracted": total_chars_extracted,
                "chars_per_page_mean": chars_per_page_mean,
                "empty_page_ratio": empty_page_ratio,
                "parser_exception": int(parser_exception),
            },
        )

    return NeedsOcrDecision(
        needs_ocr=False,
        reason="not_needed",
        metrics={
            "total_chars_extracted": total_chars_extracted,
            "chars_per_page_mean": chars_per_page_mean,
            "empty_page_ratio": empty_page_ratio,
            "parser_exception": int(parser_exception),
        },
    )
