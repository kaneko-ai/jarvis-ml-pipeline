"""PII Scanner.

Per V4.2 Sprint 3, this detects PII in text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from re import Pattern


class PIIType(Enum):
    """Types of PII."""

    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "dob"
    IP_ADDRESS = "ip_address"


@dataclass
class PIIMatch:
    """A PII match in text."""

    pii_type: PIIType
    start: int
    end: int
    text: str
    confidence: float


class PIIScanner:
    """Scans text for PII."""

    def __init__(self):
        self.patterns: dict[PIIType, Pattern] = {
            PIIType.EMAIL: re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            PIIType.PHONE: re.compile(
                r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
            ),
            PIIType.SSN: re.compile(
                r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'
            ),
            PIIType.CREDIT_CARD: re.compile(
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
            ),
            PIIType.IP_ADDRESS: re.compile(
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ),
        }

    def scan(self, text: str) -> list[PIIMatch]:
        """Scan text for PII.

        Args:
            text: Text to scan.

        Returns:
            List of PII matches.
        """
        matches = []

        for pii_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                matches.append(PIIMatch(
                    pii_type=pii_type,
                    start=match.start(),
                    end=match.end(),
                    text=match.group(),
                    confidence=0.9,
                ))

        return matches

    def has_pii(self, text: str) -> bool:
        """Check if text contains PII."""
        return len(self.scan(text)) > 0

    def get_pii_summary(self, text: str) -> dict:
        """Get summary of PII in text."""
        matches = self.scan(text)
        summary = {}

        for match in matches:
            pii_type = match.pii_type.value
            if pii_type not in summary:
                summary[pii_type] = 0
            summary[pii_type] += 1

        return {
            "has_pii": len(matches) > 0,
            "total_matches": len(matches),
            "by_type": summary,
        }
