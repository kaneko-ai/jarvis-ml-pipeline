"""Retry policy helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetryDecision:
    """Decision for retry behavior."""

    should_retry: bool
    delay_seconds: float = 0.0


class RetryPolicy:
    """Simple retry policy."""

    def __init__(self, max_attempts: int = 3, base_delay: float = 0.5) -> None:
        """Initialize policy.

        Args:
            max_attempts: Maximum retry attempts.
            base_delay: Base delay in seconds.
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay

    def decide(self, attempt: int) -> RetryDecision:
        """Decide whether to retry.

        Args:
            attempt: Current attempt number (1-based).

        Returns:
            RetryDecision with delay.
        """
        if attempt >= self.max_attempts:
            return RetryDecision(should_retry=False, delay_seconds=0.0)
        delay = self.base_delay * attempt
        return RetryDecision(should_retry=True, delay_seconds=delay)


__all__ = ["RetryDecision", "RetryPolicy"]
