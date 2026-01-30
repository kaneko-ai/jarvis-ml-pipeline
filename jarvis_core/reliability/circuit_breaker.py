"""Circuit Breaker v2.

Per RP-575, implements robust circuit breaker pattern.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import TypeVar


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitStats:
    """Circuit breaker statistics."""

    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    rejected_count: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None


@dataclass
class CircuitConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 30.0
    half_open_max_calls: int = 3
    excluded_exceptions: tuple = ()


class CircuitOpenError(Exception):
    """Raised when circuit is open."""

    def __init__(self, circuit_name: str, retry_after: float):
        self.circuit_name = circuit_name
        self.retry_after = retry_after
        super().__init__(f"Circuit '{circuit_name}' is open. Retry after {retry_after:.1f}s")


T = TypeVar("T")


class CircuitBreaker:
    """Circuit breaker for fault isolation.

    Per RP-575:
    - Three states: closed, open, half-open
    - Configurable thresholds
    - Fallback support
    - Thread-safe
    """

    def __init__(
        self,
        name: str,
        config: CircuitConfig | None = None,
        fallback: Callable[..., T] | None = None,
    ):
        self.name = name
        self.config = config or CircuitConfig()
        self.fallback = fallback

        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._half_open_calls = 0
        self._lock = threading.RLock()

    @property
    def state(self) -> CircuitState:
        """Get current state."""
        with self._lock:
            self._check_state_transition()
            return self._state

    @property
    def stats(self) -> CircuitStats:
        """Get statistics."""
        return self._stats

    def _check_state_transition(self) -> None:
        """Check and perform state transitions."""
        if self._state == CircuitState.OPEN:
            # Check if timeout has passed
            if self._stats.last_failure_time:
                elapsed = time.time() - self._stats.last_failure_time
                if elapsed >= self.config.timeout_seconds:
                    self._transition_to(CircuitState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        self._state = new_state

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
        elif new_state == CircuitState.CLOSED:
            self._stats.failure_count = 0

    def _record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            self._stats.success_count += 1
            self._stats.last_success_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)

    def _record_failure(self, is_timeout: bool = False) -> None:
        """Record a failed call."""
        with self._lock:
            self._stats.failure_count += 1
            self._stats.last_failure_time = time.time()

            if is_timeout:
                self._stats.timeout_count += 1

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._stats.failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

    def call(
        self,
        func: Callable[..., T],
        *args,
        **kwargs,
    ) -> T:
        """Execute a call through the circuit breaker.

        Args:
            func: Function to call.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Function result.

        Raises:
            CircuitOpenError: If circuit is open.
        """
        with self._lock:
            self._check_state_transition()

            if self._state == CircuitState.OPEN:
                self._stats.rejected_count += 1

                if self.fallback:
                    return self.fallback(*args, **kwargs)

                retry_after = self.config.timeout_seconds
                if self._stats.last_failure_time:
                    elapsed = time.time() - self._stats.last_failure_time
                    retry_after = max(0, self.config.timeout_seconds - elapsed)

                raise CircuitOpenError(self.name, retry_after)

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._stats.rejected_count += 1
                    raise CircuitOpenError(self.name, 1.0)

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.config.excluded_exceptions:
            # These exceptions don't count as failures
            raise
        except Exception as e:
            self._record_failure(is_timeout=isinstance(e, TimeoutError))
            raise

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator usage."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper

    def reset(self) -> None:
        """Reset the circuit breaker."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._stats = CircuitStats()
            self._half_open_calls = 0


# Global circuit breaker registry
_circuits: dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_circuit(
    name: str,
    config: CircuitConfig | None = None,
) -> CircuitBreaker:
    """Get or create a circuit breaker.

    Args:
        name: Circuit name.
        config: Optional configuration.

    Returns:
        CircuitBreaker instance.
    """
    with _registry_lock:
        if name not in _circuits:
            _circuits[name] = CircuitBreaker(name, config)
        return _circuits[name]


def circuit_breaker(
    name: str,
    config: CircuitConfig | None = None,
    fallback: Callable | None = None,
) -> Callable:
    """Decorator for circuit breaker.

    Args:
        name: Circuit name.
        config: Optional configuration.
        fallback: Optional fallback function.

    Returns:
        Decorator.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        circuit = get_circuit(name, config)
        if fallback:
            circuit.fallback = fallback

        @wraps(func)
        def wrapper(*args, **kwargs):
            return circuit.call(func, *args, **kwargs)

        wrapper.circuit = circuit
        return wrapper

    return decorator