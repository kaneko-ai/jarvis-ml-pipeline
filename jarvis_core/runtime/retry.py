"""Retry Policy.

Per PR-96, provides systematic retry with backoff.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Retry policy configuration."""

    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (Exception,)


@dataclass
class RetryResult:
    """Result of a retry operation."""

    success: bool
    value: any | None = None
    attempts: int = 0
    last_error: Exception | None = None
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def calculate_backoff(
    attempt: int,
    policy: RetryPolicy,
) -> float:
    """Calculate backoff delay for an attempt."""
    delay = policy.base_delay_seconds * (policy.exponential_base**attempt)
    delay = min(delay, policy.max_delay_seconds)

    if policy.jitter:
        delay *= 0.5 + random.random()

    return delay


def with_retry(
    fn: Callable[[], T],
    policy: RetryPolicy | None = None,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> RetryResult:
    """Execute function with retry.

    Args:
        fn: Function to execute.
        policy: Retry policy.
        on_retry: Callback on each retry (attempt, error).

    Returns:
        RetryResult with success status and value/errors.
    """
    if policy is None:
        policy = RetryPolicy()

    errors = []

    for attempt in range(policy.max_retries + 1):
        try:
            result = fn()
            return RetryResult(
                success=True,
                value=result,
                attempts=attempt + 1,
                errors=errors,
            )
        except policy.retryable_exceptions as e:
            errors.append(f"Attempt {attempt + 1}: {type(e).__name__}: {e}")

            if attempt < policy.max_retries:
                delay = calculate_backoff(attempt, policy)

                if on_retry:
                    on_retry(attempt + 1, e)

                time.sleep(delay)
            else:
                return RetryResult(
                    success=False,
                    attempts=attempt + 1,
                    last_error=e,
                    errors=errors,
                )

    return RetryResult(success=False, errors=errors)


class CircuitOpen(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreakerRetry:
    """Combines retry with circuit breaker."""

    def __init__(
        self,
        policy: RetryPolicy,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        self.policy = policy
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self._is_open = False

    @property
    def is_open(self) -> bool:
        if not self._is_open:
            return False

        # Check if recovery timeout has passed
        if self.last_failure_time:
            elapsed = time.time() - self.last_failure_time
            if elapsed > self.recovery_timeout:
                self._is_open = False
                self.failure_count = 0
                return False

        return True

    def execute(self, fn: Callable[[], T]) -> RetryResult:
        """Execute with circuit breaker."""
        if self.is_open:
            raise CircuitOpen(
                f"Circuit is open after {self.failure_count} failures. "
                f"Recovery in {self.recovery_timeout - (time.time() - self.last_failure_time):.1f}s"
            )

        result = with_retry(fn, self.policy)

        if result.success:
            self.failure_count = 0
        else:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self._is_open = True

        return result