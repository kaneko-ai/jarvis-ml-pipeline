"""PII anonymization utilities."""

from __future__ import annotations

import logging

from jarvis_core.security.pii_detector import PIIDetection

logger = logging.getLogger(__name__)


def anonymize(text: str, detections: list[PIIDetection], strategy: str = "mask") -> str:
    """Anonymize detected PII in text.

    Args:
        text: Original text.
        detections: List of PII detections.
        strategy: "mask", "replace", or "remove".

    Returns:
        Anonymized text.
    """
    replacement = {
        "mask": lambda value: "*" * len(value),
        "replace": lambda value: f"[{value.split('@')[0] if '@' in value else 'REDACTED'}]",
        "remove": lambda value: "",
    }

    if strategy not in replacement:
        raise ValueError(f"Unknown strategy: {strategy}")

    anonymized = text
    for detection in sorted(detections, key=lambda d: d.start, reverse=True):
        before = anonymized[: detection.start]
        after = anonymized[detection.end :]
        token = replacement[strategy](detection.value)
        anonymized = before + token + after
        logger.info("Anonymized %s at %s-%s", detection.type, detection.start, detection.end)

    return anonymized
