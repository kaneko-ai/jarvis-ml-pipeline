"""Retry with Backoff.

Per RP-576, implements exponential backoff retry.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Retry configuration."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)


class RetryExhaustedError(Exception):
    """Raised when all retries are exhausted."""

    def __init__(self, attempts: int, last_exception: Exception):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(f"Retry exhausted after {attempts} attempts: {last_exception}")


def calculate_delay(
    attempt: int,
    config: RetryConfig,
) -> float:
    """Calculate delay with exponential backoff and jitter.

    Args:
        attempt: Current attempt number (0-indexed).
        config: Retry configuration.

    Returns:
        Delay in seconds.
    """
    delay = config.base_delay * (config.exponential_base**attempt)
    delay = min(delay, config.max_delay)

    if config.jitter:
        jitter_range = delay * config.jitter_factor
        delay += random.uniform(-jitter_range, jitter_range)

    return max(0, delay)


def retry_with_backoff(
    config: RetryConfig | None = None,
    on_retry: Callable[[int, Exception, float], None] | None = None,
) -> Callable:
    """Decorator for retry with exponential backoff.

    Args:
        config: Retry configuration.
        on_retry: Callback on each retry.

    Returns:
        Decorator.
    """
    config = config or RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Exception | None = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt >= config.max_retries:
                        raise RetryExhaustedError(attempt + 1, e) from e

                    delay = calculate_delay(attempt, config)

                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"after {delay:.2f}s: {e}"
                    )

                    if on_retry:
                        on_retry(attempt + 1, e, delay)

                    time.sleep(delay)

            # Should not reach here
            raise RetryExhaustedError(config.max_retries, last_exception)

        return wrapper

    return decorator


class RetryContext:
    """Context manager for retry logic.

    Usage:
        with RetryContext(max_retries=3) as retry:
            for attempt in retry:
                try:
                    result = do_something()
                    break
                except Exception as e:
                    retry.handle_exception(e)
    """

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()
        self._attempt = 0
        self._exhausted = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def __iter__(self):
        while self._attempt <= self.config.max_retries:
            yield self._attempt
            self._attempt += 1
        self._exhausted = True

    def handle_exception(self, exception: Exception) -> None:
        """Handle an exception, sleeping before next attempt."""
        if self._attempt >= self.config.max_retries:
            raise RetryExhaustedError(self._attempt + 1, exception) from exception

        if not isinstance(exception, self.config.retryable_exceptions):
            raise exception

        delay = calculate_delay(self._attempt, self.config)
        time.sleep(delay)


async def async_retry_with_backoff(
    func: Callable[..., T],
    config: RetryConfig | None = None,
    *args,
    **kwargs,
) -> T:
    """Async retry with exponential backoff.

    Args:
        func: Async function to retry.
        config: Retry configuration.
        *args: Positional arguments.
        **kwargs: Keyword arguments.

    Returns:
        Function result.
    """
    import asyncio

    config = config or RetryConfig()
    last_exception: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e

            if attempt >= config.max_retries:
                raise RetryExhaustedError(attempt + 1, e) from e

            delay = calculate_delay(attempt, config)
            await asyncio.sleep(delay)

    raise RetryExhaustedError(config.max_retries, last_exception)