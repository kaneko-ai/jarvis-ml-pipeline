"""Prompt injection guard."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class InjectionCheckResult:
    is_suspicious: bool
    patterns_detected: list[str]
    sanitized_input: str


PATTERNS = {
    "system_override": re.compile(r"ignore (all|previous) instructions", re.IGNORECASE),
    "role_change": re.compile(r"you are now|act as", re.IGNORECASE),
    "instruction_ignore": re.compile(r"disregard.*rules", re.IGNORECASE),
}


def check_injection(user_input: str) -> InjectionCheckResult:
    """Detect prompt injection patterns and sanitize input."""
    detected = [name for name, pattern in PATTERNS.items() if pattern.search(user_input)]
    sanitized = user_input
    if detected:
        for name in detected:
            sanitized = re.sub(PATTERNS[name], "[REDACTED]", sanitized)
    return InjectionCheckResult(
        is_suspicious=bool(detected),
        patterns_detected=detected,
        sanitized_input=sanitized,
    )
