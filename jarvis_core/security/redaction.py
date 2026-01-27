from __future__ import annotations
import logging
import re

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
                    self.replacement_char if c.isalnum() else c for c in match.text
                )
            else:
                replacement = self.replacement_char * len(match.text)

            result = result[: match.start] + replacement + result[match.end :]

            # Log redaction
            self.redaction_log.append(
                {
                    "type": match.pii_type.value,
                    "position": match.start,
                    "length": len(match.text),
                }
            )

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
                    (
                        self.redact_dict(v)
                        if isinstance(v, dict)
                        else self.redact_text(v) if isinstance(v, str) else v
                    )
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




class RedactingFilter(logging.Filter):
    """Logging filter that redacts sensitive information from log records."""

    def __init__(self, patterns: list[str] | None = None):
        super().__init__()
        self.redactor = Redactor(preserve_format=False)
        self.patterns = patterns or []
        # Add common secret patterns with non-greedy matches
        self.patterns.extend(
            [
                r"API_KEY=['\"](.*?)['\"]",
                r"Bearer\s+([a-zA-Z0-9\._\-]+)",
                r"password=['\"](.*?)['\"]",
            ]
        )

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact the message of the log record."""
        if not isinstance(record.msg, str):
            return True

        # 1. Redact based on explicit patterns
        msg = record.msg
        for pattern in self.patterns:

            def redact_match(m):
                # Replace the content of group(1) within the matched string from group(0)
                full_match = m.group(0)
                secret = m.group(1)
                if not secret:
                    return full_match
                # We replace exactly the secret part in the reported full_match string
                return full_match.replace(secret, "********")

            msg = re.sub(pattern, redact_match, msg)

        # 2. Redact general PII
        record.msg = self.redactor.redact_text(msg)

        # Also redact from arguments if they are strings
        if record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    # Apply explicit patterns to args too
                    redacted_arg = arg
                    for pattern in self.patterns:

                        def redact_match(m):
                            full_match = m.group(0)
                            secret = m.group(1)
                            return full_match.replace(secret, "********") if secret else full_match

                        redacted_arg = re.sub(pattern, redact_match, redacted_arg)
                    new_args.append(self.redactor.redact_text(redacted_arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)

        return True


def redact_text(text: str, preserve_format: bool = True) -> str:
    """Convenience function to redact PII from text."""
    redactor = Redactor(preserve_format=preserve_format)
    return redactor.redact_text(text)


def setup_logging_redaction(patterns: list[str] | None = None):
    """Setup redaction for all existing handlers."""
    redact_filter = RedactingFilter(patterns)
    root = logging.getLogger()
    for handler in root.handlers:
        handler.addFilter(redact_filter)

    # Also add to JARVIS specific loggers
    logging.getLogger("jarvis_core").addFilter(redact_filter)
    logging.getLogger("jarvis_web").addFilter(redact_filter)
