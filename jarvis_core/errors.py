"""Error Taxonomy & Exit Codes.

Per V4-P06, this defines error types and standardized exit codes.
"""

from __future__ import annotations


class JarvisError(Exception):
    """Base error for all JARVIS errors."""

    exit_code = 1
    category = "general"

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(JarvisError):
    """Input validation error."""

    exit_code = 10
    category = "validation"


class EvidenceError(JarvisError):
    """Evidence-related error."""

    exit_code = 20
    category = "evidence"


class IntegrationError(JarvisError):
    """External integration error."""

    exit_code = 30
    category = "integration"


class TimeoutError(JarvisError):
    """Operation timeout."""

    exit_code = 40
    category = "timeout"


class ConfigError(JarvisError):
    """Configuration error."""

    exit_code = 50
    category = "config"


class BundleError(JarvisError):
    """Bundle operation error."""

    exit_code = 60
    category = "bundle"


class TruthError(JarvisError):
    """Truthfulness violation."""

    exit_code = 70
    category = "truth"


# Exit code documentation
EXIT_CODES = {
    0: "Success",
    1: "General error",
    10: "Validation error (bad input)",
    20: "Evidence error (missing/invalid evidence)",
    30: "Integration error (external service failure)",
    40: "Timeout error",
    50: "Configuration error",
    60: "Bundle error",
    70: "Truthfulness error",
}


def get_exit_code_meaning(code: int) -> str:
    """Get human-readable meaning of exit code."""
    return EXIT_CODES.get(code, "Unknown error")