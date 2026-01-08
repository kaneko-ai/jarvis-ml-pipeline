"""Telemetry Redaction.

Per PR-71, scrubs sensitive data from logs.
"""
from __future__ import annotations

import re
from typing import Any

# Patterns to redact
REDACTION_PATTERNS = [
    # API keys
    (r"([A-Za-z0-9_-]{20,})", "***API_KEY***"),  # Generic long tokens
    (r"(sk-[A-Za-z0-9]{32,})", "***OPENAI_KEY***"),  # OpenAI
    (r"(AIza[A-Za-z0-9_-]{35})", "***GOOGLE_KEY***"),  # Google

    # Personal info
    (r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "***EMAIL***"),  # Email
    (r"\b\d{3}[-.]?\d{4}[-.]?\d{4}\b", "***PHONE***"),  # Phone

    # Credentials
    (r"(password|passwd|pwd)\s*[=:]\s*\S+", "***PASSWORD***"),
    (r"(token|secret|key)\s*[=:]\s*\S+", "***SECRET***"),

    # Common env vars
    (r"NCBI_API_KEY=\S+", "NCBI_API_KEY=***"),
    (r"UNPAYWALL_EMAIL=\S+", "UNPAYWALL_EMAIL=***"),
]


def redact_string(text: str) -> str:
    """Redact sensitive patterns from a string."""
    result = text
    for pattern, replacement in REDACTION_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def redact_dict(data: dict[str, Any], depth: int = 0, max_depth: int = 5) -> dict[str, Any]:
    """Recursively redact sensitive data from a dictionary."""
    if depth > max_depth:
        return data

    result = {}
    for key, value in data.items():
        # Redact by key name
        key_lower = key.lower()
        if any(s in key_lower for s in ["password", "secret", "key", "token", "credential"]):
            result[key] = "***REDACTED***"
        elif isinstance(value, str):
            result[key] = redact_string(value)
        elif isinstance(value, dict):
            result[key] = redact_dict(value, depth + 1, max_depth)
        elif isinstance(value, list):
            result[key] = [
                redact_dict(v, depth + 1, max_depth) if isinstance(v, dict)
                else redact_string(v) if isinstance(v, str)
                else v
                for v in value
            ]
        else:
            result[key] = value

    return result
