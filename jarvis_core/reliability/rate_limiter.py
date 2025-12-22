"""Rate Limiter v2.

Per RP-563, implements token bucket rate limiting.
"""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Optional
from functools import wraps


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    
    requests_per_second: float = 10.0
    burst_size: int = 20
    per_user: bool = True


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    
    allowed: bool
    remaining: int
    reset_at: float
    retry_after: Optional[float] = None


class TokenBucket:
    """Token bucket rate limiter.
    
    Per RP-563:
    - Token bucket algorithm
    - Per-user limits
    - Burst handling
    """
    
    def __init__(
        self,
        rate: float = 10.0,
        capacity: int = 20,
    ):
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_update = time.time()
        self._lock = threading.Lock()
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_update
        self._tokens = min(
            self.capacity,
            self._tokens + elapsed * self.rate,
        )
        self._last_update = now
    
    def try_acquire(self, tokens: int = 1) -> RateLimitResult:
        """Try to acquire tokens.
        
        Args:
            tokens: Number of tokens to acquire.
            
        Returns:
            RateLimitResult.
        """
        with self._lock:
            self._refill()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return RateLimitResult(
                    allowed=True,
                    remaining=int(self._tokens),
                    reset_at=time.time() + (self.capacity - self._tokens) / self.rate,
                )
            else:
                # Calculate wait time
                deficit = tokens - self._tokens
                wait_time = deficit / self.rate
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=time.time() + wait_time,
                    retry_after=wait_time,
                )
    
    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """Acquire tokens, blocking if necessary.
        
        Args:
            tokens: Number of tokens.
            timeout: Maximum wait time.
            
        Returns:
            True if acquired.
        """
        start = time.time()
        
        while True:
            result = self.try_acquire(tokens)
            
            if result.allowed:
                return True
            
            if timeout is not None:
                elapsed = time.time() - start
                if elapsed + result.retry_after > timeout:
                    return False
            
            time.sleep(min(result.retry_after, 0.1))


class RateLimiter:
    """Multi-key rate limiter.
    
    Manages rate limits per user/API key.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._buckets: Dict[str, TokenBucket] = {}
        self._global_bucket = TokenBucket(
            rate=self.config.requests_per_second * 10,
            capacity=self.config.burst_size * 10,
        )
        self._lock = threading.Lock()
    
    def _get_bucket(self, key: str) -> TokenBucket:
        """Get or create bucket for key."""
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(
                    rate=self.config.requests_per_second,
                    capacity=self.config.burst_size,
                )
            return self._buckets[key]
    
    def check(self, key: Optional[str] = None) -> RateLimitResult:
        """Check rate limit.
        
        Args:
            key: User/API key (uses global if None).
            
        Returns:
            RateLimitResult.
        """
        # Check global limit
        global_result = self._global_bucket.try_acquire()
        if not global_result.allowed:
            return global_result
        
        # Check per-key limit
        if key and self.config.per_user:
            bucket = self._get_bucket(key)
            return bucket.try_acquire()
        
        return global_result
    
    def is_allowed(self, key: Optional[str] = None) -> bool:
        """Check if request is allowed.
        
        Args:
            key: User/API key.
            
        Returns:
            True if allowed.
        """
        return self.check(key).allowed
    
    def wait(
        self,
        key: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait for rate limit.
        
        Args:
            key: User/API key.
            timeout: Maximum wait time.
            
        Returns:
            True if acquired.
        """
        bucket = self._get_bucket(key) if key else self._global_bucket
        return bucket.acquire(timeout=timeout)


class RateLimitError(Exception):
    """Rate limit exceeded error."""
    
    def __init__(self, result: RateLimitResult):
        self.result = result
        super().__init__(
            f"Rate limit exceeded. Retry after {result.retry_after:.2f}s"
        )


def rate_limit(
    config: Optional[RateLimitConfig] = None,
    key_func: Optional[callable] = None,
) -> callable:
    """Decorator for rate limiting.
    
    Args:
        config: Rate limit configuration.
        key_func: Function to extract key from args.
        
    Returns:
        Decorator.
    """
    limiter = RateLimiter(config)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = key_func(*args, **kwargs) if key_func else None
            result = limiter.check(key)
            
            if not result.allowed:
                raise RateLimitError(result)
            
            return func(*args, **kwargs)
        
        wrapper.limiter = limiter
        return wrapper
    
    return decorator
