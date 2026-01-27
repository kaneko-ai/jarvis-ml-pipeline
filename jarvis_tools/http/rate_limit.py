"""HTTP Rate Limiter.

Per RP-107, provides domain-specific rate limiting.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Optional
from collections import defaultdict


@dataclass
class RateLimitConfig:
    """Rate limit configuration per domain."""

    min_interval_seconds: float = 1.0  # Minimum time between requests
    max_retries: int = 3
    backoff_base: float = 2.0
    max_backoff_seconds: float = 60.0


# Default configs for known domains
DEFAULT_CONFIGS: Dict[str, RateLimitConfig] = {
    "ncbi.nlm.nih.gov": RateLimitConfig(min_interval_seconds=0.34),  # 3 req/sec with API key
    "api.unpaywall.org": RateLimitConfig(min_interval_seconds=1.0),
    "doi.org": RateLimitConfig(min_interval_seconds=0.5),
}


class RateLimiter:
    """Thread-safe rate limiter for HTTP requests."""

    def __init__(self, default_config: Optional[RateLimitConfig] = None):
        self._last_request: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()
        self._default_config = default_config or RateLimitConfig()
        self._domain_configs: Dict[str, RateLimitConfig] = dict(DEFAULT_CONFIGS)

    def get_config(self, domain: str) -> RateLimitConfig:
        """Get config for a domain."""
        domain = domain.lower()
        return self._domain_configs.get(domain, self._default_config)

    def set_config(self, domain: str, config: RateLimitConfig) -> None:
        """Set config for a domain."""
        self._domain_configs[domain.lower()] = config

    def wait_if_needed(self, domain: str) -> float:
        """Wait if needed to respect rate limit. Returns wait time."""
        domain = domain.lower()
        config = self.get_config(domain)

        with self._lock:
            now = time.time()
            last = self._last_request[domain]
            elapsed = now - last

            if elapsed < config.min_interval_seconds:
                wait_time = config.min_interval_seconds - elapsed
                self._lock.release()
                try:
                    time.sleep(wait_time)
                finally:
                    self._lock.acquire()
                self._last_request[domain] = time.time()
                return wait_time
            else:
                self._last_request[domain] = now
                return 0.0

    def calculate_backoff(self, domain: str, attempt: int) -> float:
        """Calculate backoff delay for retry attempt."""
        config = self.get_config(domain)
        delay = config.min_interval_seconds * (config.backoff_base**attempt)
        return min(delay, config.max_backoff_seconds)

    def should_retry(self, domain: str, attempt: int) -> bool:
        """Check if retry is allowed."""
        config = self.get_config(domain)
        return attempt < config.max_retries


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None
_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter."""
    global _rate_limiter
    with _limiter_lock:
        if _rate_limiter is None:
            _rate_limiter = RateLimiter()
        return _rate_limiter


def rate_limit(domain: str) -> float:
    """Apply rate limiting for a domain. Returns wait time."""
    return get_rate_limiter().wait_if_needed(domain)


@dataclass
class RateLimitStats:
    """Statistics for rate limiting."""

    domain: str
    total_requests: int = 0
    total_wait_seconds: float = 0.0
    retries: int = 0


class RateLimitTracker:
    """Track rate limit statistics per domain."""

    def __init__(self):
        self._stats: Dict[str, RateLimitStats] = {}
        self._lock = threading.Lock()

    def record(self, domain: str, wait_time: float, is_retry: bool = False) -> None:
        """Record a request."""
        domain = domain.lower()
        with self._lock:
            if domain not in self._stats:
                self._stats[domain] = RateLimitStats(domain=domain)

            self._stats[domain].total_requests += 1
            self._stats[domain].total_wait_seconds += wait_time
            if is_retry:
                self._stats[domain].retries += 1

    def get_stats(self, domain: str) -> Optional[RateLimitStats]:
        """Get stats for a domain."""
        return self._stats.get(domain.lower())

    def get_all_stats(self) -> Dict[str, RateLimitStats]:
        """Get all stats."""
        return dict(self._stats)
