"""Performance Optimization Utilities for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 3.5: 最適化
Provides utilities for memory, performance, and resource optimization.
"""

from __future__ import annotations

import gc
import logging
import sys
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache, wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class PerformanceMetrics:
    """Performance measurement results."""

    name: str
    execution_time_ms: float
    memory_before_mb: float
    memory_after_mb: float
    memory_delta_mb: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "memory_before_mb": round(self.memory_before_mb, 2),
            "memory_after_mb": round(self.memory_after_mb, 2),
            "memory_delta_mb": round(self.memory_delta_mb, 2),
        }


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback without psutil
        return sys.getsizeof(gc.get_objects()) / (1024 * 1024)


@contextmanager
def measure_performance(name: str = "operation") -> Generator[PerformanceMetrics, None, None]:
    """Context manager to measure performance.

    Usage:
        with measure_performance("my_operation") as metrics:
            # do work
        print(f"Time: {metrics.execution_time_ms}ms")
    """
    gc.collect()
    memory_before = get_memory_usage_mb()
    start_time = time.perf_counter()

    metrics = PerformanceMetrics(
        name=name,
        execution_time_ms=0,
        memory_before_mb=memory_before,
        memory_after_mb=0,
        memory_delta_mb=0,
    )

    try:
        yield metrics
    finally:
        end_time = time.perf_counter()
        memory_after = get_memory_usage_mb()

        metrics.execution_time_ms = (end_time - start_time) * 1000
        metrics.memory_after_mb = memory_after
        metrics.memory_delta_mb = memory_after - memory_before

        logger.debug(
            f"{name}: {metrics.execution_time_ms:.2f}ms, "
            f"memory delta: {metrics.memory_delta_mb:+.2f}MB"
        )


def timed(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to time function execution."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"{func.__name__}: {elapsed:.2f}ms")
        return result

    return wrapper


def memoize(maxsize: int = 128):
    """Memoization decorator with size limit.

    Args:
        maxsize: Maximum cache size.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        return lru_cache(maxsize=maxsize)(func)

    return decorator


class BatchProcessor:
    """Process items in batches for memory efficiency."""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    def process(
        self,
        items: list[Any],
        processor: Callable[[list[Any]], list[Any]],
        show_progress: bool = False,
    ) -> list[Any]:
        """Process items in batches.

        Args:
            items: Items to process.
            processor: Function to process each batch.
            show_progress: Log progress.

        Returns:
            Processed results.
        """
        results = []
        total = len(items)

        for i in range(0, total, self.batch_size):
            batch = items[i : i + self.batch_size]
            batch_results = processor(batch)
            results.extend(batch_results)

            if show_progress:
                progress = min(i + self.batch_size, total)
                logger.info(f"Processed {progress}/{total} items")

            # Allow GC between batches
            gc.collect()

        return results


class LazyLoader:
    """Lazy loading wrapper for expensive resources."""

    def __init__(self, loader: Callable[[], T]):
        self._loader = loader
        self._value: T | None = None
        self._loaded = False

    @property
    def value(self) -> T:
        if not self._loaded:
            self._value = self._loader()
            self._loaded = True
        return self._value  # type: ignore

    def is_loaded(self) -> bool:
        return self._loaded

    def unload(self) -> None:
        """Unload to free memory."""
        self._value = None
        self._loaded = False
        gc.collect()


class MemoryManager:
    """Manage memory usage and cleanup."""

    def __init__(self, threshold_mb: float = 500):
        self.threshold_mb = threshold_mb
        self._resources: list[LazyLoader] = []

    def register(self, resource: LazyLoader) -> None:
        """Register a lazy resource for memory management."""
        self._resources.append(resource)

    def check_memory(self) -> bool:
        """Check if memory usage is below threshold."""
        current = get_memory_usage_mb()
        return current < self.threshold_mb

    def cleanup(self, force: bool = False) -> int:
        """Cleanup resources if memory is high.

        Returns:
            Number of resources unloaded.
        """
        if not force and self.check_memory():
            return 0

        unloaded = 0
        for resource in self._resources:
            if resource.is_loaded():
                resource.unload()
                unloaded += 1

        gc.collect()
        logger.info(f"Cleaned up {unloaded} resources")
        return unloaded

    def status(self) -> dict[str, Any]:
        """Get memory status."""
        current = get_memory_usage_mb()
        return {
            "current_mb": round(current, 2),
            "threshold_mb": self.threshold_mb,
            "under_threshold": current < self.threshold_mb,
            "registered_resources": len(self._resources),
            "loaded_resources": sum(1 for r in self._resources if r.is_loaded()),
        }


class ResponseCache:
    """In-memory cache with TTL and size limits for API responses."""

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple] = {}  # key -> (value, expiry)

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]
        if expiry < time.time():
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        expiry = time.time() + (ttl or self.default_ttl)
        self._cache[key] = (value, expiry)

    def _evict_oldest(self) -> None:
        """Evict oldest entries."""
        # Remove expired first
        current_time = time.time()
        expired = [k for k, (_, exp) in self._cache.items() if exp < current_time]
        for k in expired:
            del self._cache[k]

        # If still full, remove 10% oldest
        if len(self._cache) >= self.max_size:
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][1])
            for k in sorted_keys[: len(sorted_keys) // 10 + 1]:
                del self._cache[k]

    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()

    def stats(self) -> dict[str, Any]:
        """Get cache stats."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
        }


# Global instances
_memory_manager: MemoryManager | None = None
_response_cache: ResponseCache | None = None


def get_memory_manager() -> MemoryManager:
    """Get global memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def get_response_cache() -> ResponseCache:
    """Get global response cache."""
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache()
    return _response_cache
