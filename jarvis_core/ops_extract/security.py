"""Security helpers for ops_extract artifacts and logs."""

from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from .contracts import OpsExtractConfig

REDACT_KEYS = {"token", "secret", "password", "access_key", "refresh"}


def mask_secret(value: str) -> str:
    raw = str(value or "")
    if not raw:
        return ""
    if len(raw) <= 6:
        return "***"
    return f"{raw[:2]}***{raw[-2:]}"


def redact_sensitive_text(text: str) -> str:
    if not text:
        return text
    masked = re.sub(r"Bearer\s+[A-Za-z0-9._\-]+", "Bearer ***", text, flags=re.IGNORECASE)
    masked = re.sub(
        r"(access_token|refresh_token|token)\s*[:=]\s*['\"]?([A-Za-z0-9._\-]+)",
        r"\1=***",
        masked,
        flags=re.IGNORECASE,
    )
    return masked


def redact_sensitive_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        output: dict[str, Any] = {}
        for key, value in payload.items():
            key_lower = str(key).lower()
            if any(secret_key in key_lower for secret_key in REDACT_KEYS):
                output[key] = "***redacted***" if value else value
            else:
                output[key] = redact_sensitive_payload(value)
        return output
    if isinstance(payload, list):
        return [redact_sensitive_payload(item) for item in payload]
    if isinstance(payload, str):
        return redact_sensitive_text(payload)
    return payload


def masked_ops_extract_config(config: OpsExtractConfig) -> dict[str, Any]:
    return redact_sensitive_payload(asdict(config))
