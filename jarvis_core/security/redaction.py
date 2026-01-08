"""Redaction.

Per V4.2 Sprint 3, this redacts PII from text.
"""
from __future__ import annotations

from .pii_scan import PIIScanner


class Redactor:
    """Redacts PII from text and structured data."""

    def __init__(
        self,
        replacement_char: str = "█",
        preserve_format: bool = True,
    ):
        self.scanner = PIIScanner()
        self.replacement_char = replacement_char
        self.preserve_format = preserve_format
        self.redaction_log: list[dict] = []

    def redact_text(self, text: str) -> str:
        """Redact PII from text.

        Args:
            text: Text to redact.

        Returns:
            Redacted text.
        """
        matches = self.scanner.scan(text)

        if not matches:
            return text

        # Sort by position (reverse) to maintain indices
        matches.sort(key=lambda m: m.start, reverse=True)

        result = text
        for match in matches:
            if self.preserve_format:
                # Preserve format (e.g., ###-###-#### for SSN)
                replacement = "".join(
                    self.replacement_char if c.isalnum() else c
                    for c in match.text
                )
            else:
                replacement = self.replacement_char * len(match.text)

            result = result[:match.start] + replacement + result[match.end:]

            # Log redaction
            self.redaction_log.append({
                "type": match.pii_type.value,
                "position": match.start,
                "length": len(match.text),
            })

        return result

    def redact_dict(self, data: dict) -> dict:
        """Redact PII from dictionary.

        Args:
            data: Dictionary to redact.

        Returns:
            Redacted dictionary.
        """
        result = {}

        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.redact_text(value)
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self.redact_dict(v) if isinstance(v, dict)
                    else self.redact_text(v) if isinstance(v, str)
                    else v
                    for v in value
                ]
            else:
                result[key] = value

        return result

    def get_redaction_summary(self) -> dict:
        """Get summary of redactions performed."""
        by_type = {}
        for log in self.redaction_log:
            t = log["type"]
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "total_redactions": len(self.redaction_log),
            "by_type": by_type,
        }


def redact_text(text: str, preserve_format: bool = True) -> str:
    """Convenience function to redact PII from text."""
    redactor = Redactor(preserve_format=preserve_format)
    return redactor.redact_text(text)
