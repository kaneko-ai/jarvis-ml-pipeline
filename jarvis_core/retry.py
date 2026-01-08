"""Retry policy definitions for ExecutionEngine self-healing loops."""

from __future__ import annotations

from dataclasses import dataclass

from .validation import EvaluationResult


@dataclass
class RetryDecision:
    """Represents whether another attempt should be scheduled."""

    should_retry: bool
    attempt: int
    max_attempts: int
    reason: str | None = None


@dataclass
class RetryPolicy:
    """Simple capped retry policy based on evaluation outcomes."""

    max_attempts: int = 1

    def decide(self, evaluation: EvaluationResult, attempt: int) -> RetryDecision:
        if not evaluation.ok and attempt < self.max_attempts:
            return RetryDecision(
                should_retry=True,
                attempt=attempt,
                max_attempts=self.max_attempts,
                reason="validation_failed",
            )
        return RetryDecision(
            should_retry=False,
            attempt=attempt,
            max_attempts=self.max_attempts,
            reason=None if evaluation.ok else "max_attempts_reached",
        )
