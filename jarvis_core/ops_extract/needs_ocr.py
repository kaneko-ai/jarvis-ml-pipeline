"""Rule-based OCR necessity decision."""

from __future__ import annotations

from dataclasses import dataclass
import unicodedata
from typing import Any

from .contracts import OpsExtractThresholds


@dataclass(frozen=True)
class NeedsOcrDecision:
    needs_ocr: bool
    reason: str
    metrics: dict[str, Any]


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


def unicode_category_distribution(text: str) -> dict[str, float]:
    text = text or ""
    total = max(len(text), 1)
    counts = {
        "han": 0,
        "kana": 0,
        "latin": 0,
        "digit": 0,
        "other": 0,
    }
    for ch in text:
        code = ord(ch)
        category = unicodedata.category(ch)
        if 0x4E00 <= code <= 0x9FFF:
            counts["han"] += 1
        elif 0x3040 <= code <= 0x30FF:
            counts["kana"] += 1
        elif ch.isascii() and ch.isalpha():
            counts["latin"] += 1
        elif category.startswith("N"):
            counts["digit"] += 1
        else:
            counts["other"] += 1
    return {key: round(value / total, 6) for key, value in counts.items()}


def normalize_extraction_exceptions(
    exceptions_in_text_extract: list[Any] | None,
) -> list[str]:
    if not exceptions_in_text_extract:
        return []
    codes: list[str] = []
    for item in exceptions_in_text_extract:
        raw = ""
        if isinstance(item, dict):
            raw = " ".join(
                [
                    str(item.get("category", "")),
                    str(item.get("code", "")),
                    str(item.get("message", "")),
                ]
            ).lower()
        else:
            raw = str(item).lower()
        if any(token in raw for token in {"parser", "parse", "pdf"}):
            if "parser_fail" not in codes:
                codes.append("parser_fail")
            continue
        if any(token in raw for token in {"encoding", "unicode", "codec", "decode"}):
            if "encoding_fail" not in codes:
                codes.append("encoding_fail")
            continue
        if raw.strip() and "other_exception" not in codes:
            codes.append("other_exception")
    return codes


def decide_needs_ocr(
    *,
    total_chars_extracted: int,
    chars_per_page_mean: float,
    empty_page_ratio: float,
    exceptions_in_text_extract: list[Any] | None = None,
    extraction_exceptions: list[str] | None = None,
    unicode_distribution: dict[str, float] | None = None,
    thresholds: OpsExtractThresholds | None = None,
) -> NeedsOcrDecision:
    """Apply threshold-based OCR decision rules."""
    thresholds = thresholds or OpsExtractThresholds()
    parser_exception = _has_parser_exception(exceptions_in_text_extract)
    normalized_exceptions = extraction_exceptions or normalize_extraction_exceptions(
        exceptions_in_text_extract
    )
    unicode_distribution = unicode_distribution or {}

    base_metrics = {
        "total_chars_extracted": total_chars_extracted,
        "chars_per_page_mean": chars_per_page_mean,
        "empty_page_ratio": empty_page_ratio,
        "parser_exception": int(parser_exception),
        "extraction_exceptions": normalized_exceptions,
        "unicode_category_distribution": unicode_distribution,
    }

    if total_chars_extracted < thresholds.min_total_chars:
        return NeedsOcrDecision(
            needs_ocr=True,
            reason="total_chars_below_threshold",
            metrics=base_metrics,
        )

    if (
        chars_per_page_mean < thresholds.min_chars_per_page
        and empty_page_ratio > thresholds.empty_page_ratio_threshold
    ):
        return NeedsOcrDecision(
            needs_ocr=True,
            reason="low_chars_and_high_empty_pages",
            metrics=base_metrics,
        )

    if parser_exception or any(
        exc in {"parser_fail", "encoding_fail"} for exc in normalized_exceptions
    ):
        return NeedsOcrDecision(
            needs_ocr=True,
            reason="extraction_exception_detected",
            metrics=base_metrics,
        )

    if unicode_distribution.get("other", 0.0) > 0.9 and total_chars_extracted > 0:
        return NeedsOcrDecision(
            needs_ocr=True,
            reason="unicode_distribution_anomaly",
            metrics=base_metrics,
        )

    return NeedsOcrDecision(
        needs_ocr=False,
        reason="not_needed",
        metrics=base_metrics,
    )
