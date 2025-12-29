"""Scheduler rate limiting utilities."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

from jarvis_core.reliability.rate_limiter import TokenBucket


@dataclass
class DomainLimit:
    rate_per_sec: float
    burst: int


DEFAULT_LIMITS = {
    "pubmed": DomainLimit(rate_per_sec=3.0, burst=3),
    "unpaywall": DomainLimit(rate_per_sec=1.0, burst=1),
}


class DomainRateLimiter:
    def __init__(self, limits: Optional[Dict[str, DomainLimit]] = None):
        self.limits = limits or DEFAULT_LIMITS
        self._buckets: Dict[str, TokenBucket] = {}
        self._backoff_until: Dict[str, float] = {}

    def _bucket(self, domain: str) -> TokenBucket:
        if domain not in self._buckets:
            limit = self.limits.get(domain, DomainLimit(rate_per_sec=2.0, burst=2))
            self._buckets[domain] = TokenBucket(rate=limit.rate_per_sec, capacity=limit.burst)
        return self._buckets[domain]

    def acquire(self, domain: str) -> bool:
        now = time.time()
        if self._backoff_until.get(domain, 0) > now:
            return False
        bucket = self._bucket(domain)
        result = bucket.try_acquire()
        return result.allowed

    def record_response(self, domain: str, status_code: int) -> None:
        if status_code not in {429, 503}:
            return
        current = self._backoff_until.get(domain, 0)
        delay = max(5.0, (current - time.time()) * 2)
        self._backoff_until[domain] = time.time() + delay

    def backoff_until(self, domain: str) -> float:
        return self._backoff_until.get(domain, 0)


GLOBAL_LIMITER = DomainRateLimiter()
