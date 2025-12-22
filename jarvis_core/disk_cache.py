"""Disk Cache.

Per RP-03, this provides tool-level caching for reproducibility.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Optional
from datetime import datetime


class DiskCache:
    """Disk-based cache for tool results.

    Stores results as cache_dir/{tool_name}/{input_hash}.json
    """

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.hit_count = 0
        self.miss_count = 0

    def _compute_hash(self, inputs: Any) -> str:
        """Compute hash for inputs."""
        if isinstance(inputs, str):
            content = inputs
        elif isinstance(inputs, dict):
            content = json.dumps(inputs, sort_keys=True, ensure_ascii=False)
        else:
            content = str(inputs)

        return hashlib.sha256(content.encode()).hexdigest()[:24]

    def _get_path(self, tool_name: str, input_hash: str) -> Path:
        """Get cache file path."""
        tool_dir = self.cache_dir / tool_name
        tool_dir.mkdir(parents=True, exist_ok=True)
        return tool_dir / f"{input_hash}.json"

    def get(self, tool_name: str, inputs: Any) -> Optional[Any]:
        """Get cached result.

        Args:
            tool_name: Name of the tool.
            inputs: Tool inputs.

        Returns:
            Cached result or None if miss.
        """
        input_hash = self._compute_hash(inputs)
        cache_path = self._get_path(tool_name, input_hash)

        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.hit_count += 1
                return data.get("result")
            except (json.JSONDecodeError, KeyError):
                pass

        self.miss_count += 1
        return None

    def set(self, tool_name: str, inputs: Any, result: Any) -> str:
        """Store result in cache.

        Args:
            tool_name: Name of the tool.
            inputs: Tool inputs.
            result: Result to cache.

        Returns:
            Cache key.
        """
        input_hash = self._compute_hash(inputs)
        cache_path = self._get_path(tool_name, input_hash)

        data = {
            "tool": tool_name,
            "input_hash": input_hash,
            "cached_at": datetime.now().isoformat(),
            "result": result,
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return input_hash

    def has(self, tool_name: str, inputs: Any) -> bool:
        """Check if result is cached."""
        input_hash = self._compute_hash(inputs)
        cache_path = self._get_path(tool_name, input_hash)
        return cache_path.exists()

    def invalidate(self, tool_name: str, inputs: Any) -> bool:
        """Remove cached result."""
        input_hash = self._compute_hash(inputs)
        cache_path = self._get_path(tool_name, input_hash)

        if cache_path.exists():
            cache_path.unlink()
            return True
        return False

    def clear(self, tool_name: Optional[str] = None) -> int:
        """Clear cache.

        Args:
            tool_name: If provided, only clear that tool's cache.

        Returns:
            Number of entries cleared.
        """
        count = 0

        if tool_name:
            tool_dir = self.cache_dir / tool_name
            if tool_dir.exists():
                for f in tool_dir.glob("*.json"):
                    f.unlink()
                    count += 1
        else:
            for tool_dir in self.cache_dir.iterdir():
                if tool_dir.is_dir():
                    for f in tool_dir.glob("*.json"):
                        f.unlink()
                        count += 1

        return count

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hit_count + self.miss_count
        return {
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_rate": self.hit_count / total if total > 0 else 0,
        }


# Convenience function
def get_disk_cache(cache_dir: str = "cache") -> DiskCache:
    """Get or create disk cache."""
    return DiskCache(cache_dir)
