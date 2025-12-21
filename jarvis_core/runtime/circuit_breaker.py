"""Circuit Breaker & Retry Policy.

Per V4.2 Sprint 2, this provides fault tolerance with partial result preservation.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any, Optional, List
from datetime import datetime


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


class FailureReason(Enum):
    """Categorized failure reasons."""

    INPUT = "input"         # Bad input
    CONFIG = "config"       # Configuration error
    MODEL = "model"         # Model/API error
    NETWORK = "network"     # Network failure
    TIMEOUT = "timeout"     # Timeout
    BUDGET = "budget"       # Budget exceeded
    UNKNOWN = "unknown"


@dataclass
class RetryPolicy:
    """Retry configuration."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retryable_reasons: List[FailureReason] = field(
        default_factory=lambda: [FailureReason.NETWORK, FailureReason.TIMEOUT]
    )

    def get_delay(self, attempt: int) -> float:
        """Get delay for attempt number."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)

    def should_retry(self, reason: FailureReason, attempt: int) -> bool:
        """Check if should retry."""
        if attempt >= self.max_retries:
            return False
        return reason in self.retryable_reasons


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance."""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    partial_results: List[Any] = field(default_factory=list)

    def record_success(self) -> None:
        """Record successful call."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED

    def record_failure(self, reason: FailureReason) -> None:
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def can_execute(self) -> bool:
        """Check if calls are allowed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False

        return True  # HALF_OPEN allows one test call

    def save_partial_result(self, result: Any) -> None:
        """Save partial result for recovery."""
        self.partial_results.append(result)

    def get_partial_results(self) -> List[Any]:
        """Get accumulated partial results."""
        return self.partial_results


def classify_failure(exception: Exception) -> FailureReason:
    """Classify exception into failure reason."""
    error_msg = str(exception).lower()

    if "timeout" in error_msg or "timed out" in error_msg:
        return FailureReason.TIMEOUT

    if "connection" in error_msg or "network" in error_msg:
        return FailureReason.NETWORK

    if "api" in error_msg or "rate limit" in error_msg:
        return FailureReason.MODEL

    if "budget" in error_msg or "exceeded" in error_msg:
        return FailureReason.BUDGET

    if "config" in error_msg or "invalid" in error_msg:
        return FailureReason.CONFIG

    if "input" in error_msg or "parse" in error_msg:
        return FailureReason.INPUT

    return FailureReason.UNKNOWN


def with_retry(
    fn: Callable,
    policy: RetryPolicy = None,
    breaker: CircuitBreaker = None,
) -> Any:
    """Execute function with retry and circuit breaker.

    Args:
        fn: Function to execute.
        policy: Retry policy.
        breaker: Circuit breaker.

    Returns:
        Function result.

    Raises:
        Exception if all retries fail.
    """
    policy = policy or RetryPolicy()
    breaker = breaker or CircuitBreaker()

    last_exception = None

    for attempt in range(policy.max_retries + 1):
        if not breaker.can_execute():
            raise RuntimeError(f"Circuit breaker is {breaker.state.value}")

        try:
            result = fn()
            breaker.record_success()
            return result

        except Exception as e:
            last_exception = e
            reason = classify_failure(e)
            breaker.record_failure(reason)

            if not policy.should_retry(reason, attempt):
                break

            if attempt < policy.max_retries:
                delay = policy.get_delay(attempt)
                time.sleep(delay)

    raise last_exception


@dataclass
class RecoveryResult:
    """Result after recovery attempt."""

    success: bool
    partial_results: List[Any]
    failure_reason: Optional[FailureReason]
    attempts: int
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "partial_results_count": len(self.partial_results),
            "failure_reason": self.failure_reason.value if self.failure_reason else None,
            "attempts": self.attempts,
            "error_message": self.error_message,
        }
