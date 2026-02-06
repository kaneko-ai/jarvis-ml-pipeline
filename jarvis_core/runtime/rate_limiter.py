"""Runtime rate limiter compatibility helpers."""

from __future__ import annotations

from jarvis_core.ops.rate_limiter import (
    RateLimitConfig,
    RateLimitState,
    RateLimiter,
    with_retry,
)


def get_rate_limiter(config: RateLimitConfig | None = None) -> RateLimiter:
    """Create a rate limiter instance.

    Args:
        config: Optional configuration.

    Returns:
        RateLimiter instance.
    """
    return RateLimiter(config=config)


__all__ = [
    "RateLimitConfig",
    "RateLimitState",
    "RateLimiter",
    "get_rate_limiter",
    "with_retry",
]
