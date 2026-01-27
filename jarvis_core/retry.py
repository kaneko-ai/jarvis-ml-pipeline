"""Retry policy definitions for ExecutionEngine self-healing loops."""

from __future__ import annotations
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, TypeVar, cast

from .validation import EvaluationResult


@dataclass
class RetryDecision:
    """Represents whether another attempt should be scheduled."""

    should_retry: bool
    attempt: int
    max_attempts: int
    reason: str | None = None


T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Retry policy with exponential backoff and jitter."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 10.0
    jitter: bool = True

    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute a function with retries."""
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_attempts:
                    break

                # Calculate delay with exponential backoff
                delay = min(self.max_delay, self.base_delay * (2 ** (attempt - 1)))

                # Add jitter
                if self.jitter:
                    delay = delay * (0.5 + random.random())

                time.sleep(delay)

        if last_exception:
            raise last_exception
        raise RuntimeError("Retry failed without exception")  # Should not happen

    def decide(self, evaluation: EvaluationResult, attempt: int) -> RetryDecision:
        """Decision logic for ExecutionEngine loops (LEGACY/SPECIFIC)."""
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


def with_retry(
    max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 10.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying functions."""
    policy = RetryPolicy(max_attempts=max_attempts, base_delay=base_delay, max_delay=max_delay)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return policy.execute(func, *args, **kwargs)

        return cast(Callable[..., T], wrapper)

    return decorator
