"""PII detection utilities."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class PIIDetection:
    type: str
    value: str
    start: int
    end: int
    confidence: float


PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "phone": re.compile(r"\b\d{3}[- ]?\d{3}[- ]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "address": re.compile(
        r"\b\d+\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b", re.IGNORECASE
    ),
}


def detect_pii(text: str) -> list[PIIDetection]:
    """Detect PII in text using regex and heuristics."""
    detections: list[PIIDetection] = []
    for pii_type, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            detections.append(
                PIIDetection(
                    type=pii_type,
                    value=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.8,
                )
            )
    return detections
