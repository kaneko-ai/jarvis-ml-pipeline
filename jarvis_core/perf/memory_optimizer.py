"""Memory Optimizer for JARVIS.

Per JARVIS_COMPLETION_PLAN_v3 Sprint 23: メモリ使用量削減
Provides memory optimization utilities.
"""

from __future__ import annotations

import gc
import logging
import sys
from collections.abc import Generator, Iterable
from dataclasses import dataclass
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    total_mb: float
    available_mb: float
    used_mb: float
    percent: float

    @classmethod
    def current(cls) -> MemoryStats:
        """Get current memory statistics."""
        try:
            import psutil

            mem = psutil.virtual_memory()
            return cls(
                total_mb=mem.total / (1024 * 1024),
                available_mb=mem.available / (1024 * 1024),
                used_mb=mem.used / (1024 * 1024),
                percent=mem.percent,
            )
        except ImportError:
            return cls(
                total_mb=0,
                available_mb=0,
                used_mb=0,
                percent=0,
            )


def get_object_size(obj: Any) -> int:
    """Get the size of an object in bytes.

    Args:
        obj: Object to measure

    Returns:
        Size in bytes
    """
    seen = set()

    def _sizeof(o):
        if id(o) in seen:
            return 0
        seen.add(id(o))

        size = sys.getsizeof(o)

        if isinstance(o, dict):
            size += sum(_sizeof(k) + _sizeof(v) for k, v in o.items())
        elif isinstance(o, (list, tuple, set, frozenset)):
            size += sum(_sizeof(i) for i in o)
        elif hasattr(o, "__dict__"):
            size += _sizeof(o.__dict__)

        return size

    return _sizeof(obj)


def format_size(size_bytes: int) -> str:
    """Format size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def force_gc() -> int:
    """Force garbage collection.

    Returns:
        Number of objects collected
    """
    collected = gc.collect()
    logger.debug(f"Garbage collection: {collected} objects collected")
    return collected


def batch_process(
    items: Iterable[T],
    batch_size: int = 100,
    gc_every: int = 10,
) -> Generator[list[T], None, None]:
    """Process items in batches with periodic garbage collection.

    Args:
        items: Items to process
        batch_size: Size of each batch
        gc_every: Run GC every N batches

    Yields:
        Batches of items
    """
    batch: list[T] = []
    batch_count = 0

    for item in items:
        batch.append(item)

        if len(batch) >= batch_size:
            yield batch
            batch = []
            batch_count += 1

            if batch_count % gc_every == 0:
                force_gc()

    if batch:
        yield batch


class MemoryMonitor:
    """Monitor memory usage during operations."""

    def __init__(self, threshold_mb: float = 1000):
        """Initialize monitor.

        Args:
            threshold_mb: Memory threshold in MB to trigger warning
        """
        self._threshold_mb = threshold_mb
        self._baseline: float | None = None

    def start(self) -> None:
        """Start monitoring."""
        stats = MemoryStats.current()
        self._baseline = stats.used_mb

    def check(self) -> dict[str, Any]:
        """Check current memory status.

        Returns:
            Current memory stats and delta from baseline
        """
        stats = MemoryStats.current()
        delta = stats.used_mb - (self._baseline or 0)

        result = {
            "current_mb": stats.used_mb,
            "delta_mb": delta,
            "percent": stats.percent,
            "warning": stats.used_mb > self._threshold_mb,
        }

        if result["warning"]:
            logger.warning(
                f"Memory usage high: {stats.used_mb:.1f}MB "
                f"(threshold: {self._threshold_mb:.1f}MB)"
            )

        return result

    def gc_if_needed(self, threshold_percent: float = 80) -> bool:
        """Run garbage collection if memory usage is high.

        Args:
            threshold_percent: Threshold percentage to trigger GC

        Returns:
            True if GC was triggered
        """
        stats = MemoryStats.current()

        if stats.percent > threshold_percent:
            logger.info(f"Memory at {stats.percent:.1f}%, running GC...")
            force_gc()
            return True

        return False


class LRUCache:
    """Simple LRU cache with memory limit."""

    def __init__(self, max_size: int = 100, max_memory_mb: float = 100):
        """Initialize cache.

        Args:
            max_size: Maximum number of items
            max_memory_mb: Maximum memory usage in MB
        """
        self._max_size = max_size
        self._max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self._cache: dict[str, Any] = {}
        self._access_order: list[str] = []

    def get(self, key: str) -> Any | None:
        """Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if key in self._cache:
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set item in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Check memory
        self._evict_if_needed()

        if key in self._cache:
            self._access_order.remove(key)

        self._cache[key] = value
        self._access_order.append(key)

        # Evict if over size limit
        while len(self._cache) > self._max_size:
            self._evict_oldest()

    def _evict_oldest(self) -> None:
        """Evict the oldest item."""
        if self._access_order:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]

    def _evict_if_needed(self) -> None:
        """Evict items if memory limit exceeded."""
        total_size = sum(get_object_size(v) for v in self._cache.values())

        while total_size > self._max_memory_bytes and self._access_order:
            self._evict_oldest()
            total_size = sum(get_object_size(v) for v in self._cache.values())

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._access_order.clear()

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "memory_bytes": sum(get_object_size(v) for v in self._cache.values()),
            "max_memory_bytes": self._max_memory_bytes,
        }
