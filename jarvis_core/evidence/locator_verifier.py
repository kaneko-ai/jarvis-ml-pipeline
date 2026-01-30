"""Evidence locator verification with fuzzy matching."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class VerificationResult:
    """Result for locator verification."""

    match_ratio: float
    is_valid: bool
    matched_span: str


def _best_fuzzy_match(locator: str, source_text: str) -> tuple[float, str]:
    if not locator or not source_text:
        return 0.0, ""

    if locator in source_text:
        return 1.0, locator

    window = min(len(locator), len(source_text))
    best_ratio = 0.0
    best_span = ""

    for i in range(0, len(source_text) - window + 1):
        span = source_text[i : i + window]
        ratio = SequenceMatcher(None, locator, span).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_span = span
            if best_ratio >= 0.99:
                break

    if window == len(source_text):
        return best_ratio, best_span

    for i in range(0, len(source_text) - window + 1, max(1, window // 2)):
        span = source_text[i : i + window]
        ratio = SequenceMatcher(None, locator, span).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_span = span

    return best_ratio, best_span


def verify_locator(locator: str, source_text: str) -> VerificationResult:
    """Verify locator against source text with fuzzy matching.

    Args:
        locator: Locator string to verify.
        source_text: Source text to match against.

    Returns:
        VerificationResult with match ratio, validity, and matched span.
    """
    match_ratio, matched_span = _best_fuzzy_match(locator, source_text)
    is_valid = match_ratio >= 0.8
    return VerificationResult(
        match_ratio=match_ratio,
        is_valid=is_valid,
        matched_span=matched_span,
    )
