"""Multi-Level Cache.

Per V4.2 Sprint 2, this provides L1 memory / L2 disk caching.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime


class CacheLevel(Enum):
    """Cache levels."""

    L1_MEMORY = "l1_memory"
    L2_DISK = "l2_disk"
    MISS = "miss"


@dataclass
class CacheStats:
    """Cache statistics."""

    l1_hits: int = 0
    l2_hits: int = 0
    misses: int = 0
    writes: int = 0

    def hit_rate(self) -> float:
        total = self.l1_hits + self.l2_hits + self.misses
        if total == 0:
            return 0.0
        return (self.l1_hits + self.l2_hits) / total

    def to_dict(self) -> dict:
        return {
            "l1_hits": self.l1_hits,
            "l2_hits": self.l2_hits,
            "misses": self.misses,
            "writes": self.writes,
            "hit_rate": round(self.hit_rate(), 4),
        }


class MultiLevelCache:
    """Two-level cache: L1 (memory) + L2 (disk)."""

    def __init__(
        self,
        l2_path: Optional[str] = None,
        l1_max_size: int = 1000,
    ):
        self.l1_cache: Dict[str, Any] = {}
        self.l1_max_size = l1_max_size
        self.l2_path = Path(l2_path) if l2_path else None
        self.stats = CacheStats()

        if self.l2_path:
            self.l2_path.mkdir(parents=True, exist_ok=True)

    def _l2_key_path(self, key: str) -> Path:
        """Get L2 file path for key."""
        # Use first 2 chars as subdirectory
        subdir = self.l2_path / key[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{key}.json"

    def get(self, key: str) -> tuple[Optional[Any], CacheLevel]:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Tuple of (value, cache_level).
        """
        # L1 check
        if key in self.l1_cache:
            self.stats.l1_hits += 1
            return self.l1_cache[key], CacheLevel.L1_MEMORY

        # L2 check
        if self.l2_path:
            l2_file = self._l2_key_path(key)
            if l2_file.exists():
                try:
                    with open(l2_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    value = data.get("value")

                    # Promote to L1
                    self._l1_put(key, value)

                    self.stats.l2_hits += 1
                    return value, CacheLevel.L2_DISK
                except (json.JSONDecodeError, KeyError):
                    pass

        self.stats.misses += 1
        return None, CacheLevel.MISS

    def _l1_put(self, key: str, value: Any) -> None:
        """Put value in L1, evicting if necessary."""
        # Simple LRU-like: remove oldest if full
        if len(self.l1_cache) >= self.l1_max_size:
            oldest = next(iter(self.l1_cache))
            del self.l1_cache[oldest]

        self.l1_cache[key] = value

    def put(self, key: str, value: Any, write_l2: bool = True) -> None:
        """Put value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            write_l2: Whether to write to L2.
        """
        # Always write to L1
        self._l1_put(key, value)

        # Optionally write to L2
        if write_l2 and self.l2_path:
            l2_file = self._l2_key_path(key)
            data = {
                "key": key,
                "value": value,
                "cached_at": datetime.now().isoformat(),
            }

            temp_file = l2_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            temp_file.rename(l2_file)

        self.stats.writes += 1

    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        if key in self.l1_cache:
            del self.l1_cache[key]

        if self.l2_path:
            l2_file = self._l2_key_path(key)
            if l2_file.exists():
                l2_file.unlink()

    def clear(self) -> None:
        """Clear all cache."""
        self.l1_cache.clear()

        if self.l2_path:
            for f in self.l2_path.rglob("*.json"):
                f.unlink()

    def get_stats(self) -> dict:
        """Get cache statistics."""
        return self.stats.to_dict()
