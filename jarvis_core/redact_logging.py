"""Logging utilities with sensitive data redaction (Phase 16)."""

import logging
import re
import os


class RedactionFilter(logging.Filter):
    """Filter that masks sensitive information in log records."""

    # Patterns to mask (case-insensitive)
    SENSITIVE_PATTERNS = [
        # authorization: Bearer XXX, api_key: 'XXX', etc.
        r"(?i)(authorization|api_key|ncbi_api_key|github_token|secret|token|password|auth)\s*[:=]\s*(?:Bearer\s+)?['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?",
    ]

    def __init__(self, name: str = ""):
        super().__init__(name)
        self.patterns = [re.compile(p) for p in self.SENSITIVE_PATTERNS]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact(record.msg)

        # Also redact arguments if they are strings
        if record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(self.redact(arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)

        return True

    def redact(self, text: str) -> str:
        for pattern in self.patterns:
            # Mask the captured value group (group 2)
            def mask_match(match):
                # group 1 is the key name + separator + optional Bearer
                # We want to keep everything EXCEPT the actual secret (group 2)
                full_match = match.group(0)
                secret = match.group(2)
                return full_match.replace(secret, "[REDACTED]")

            text = pattern.sub(mask_match, text)
        return text


def setup_logging(level: str = "INFO"):
    """Setup root logger with redaction filter."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] [%(request_id)s] %(message)s",
            defaults={"request_id": "none"},
        )
    )

    # Add redaction filter to handler
    handler.addFilter(RedactionFilter())

    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers
    for h in logger.handlers[:]:
        logger.removeHandler(h)

    logger.addHandler(handler)

    return logger


# Singleton-like logger access
_logger = None


def get_logger(name: str = "jarvis") -> logging.Logger:
    global _logger
    if _logger is None:
        env_level = os.environ.get("JARVIS_LOG_LEVEL", "INFO")
        setup_logging(env_level)
        _logger = logging.getLogger("jarvis")

    return logging.getLogger(name)