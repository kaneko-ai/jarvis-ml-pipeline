"""Disk-backed cache implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class DiskCache:
    """Minimal disk cache stub for compatibility."""

    def __init__(self, root: str | Path = ".cache") -> None:
        """Initialize the cache.

        Args:
            root: Root directory for cache files.
        """
        self.root = Path(root)

    def get(self, key: str) -> Any | None:
        """Get a cached value by key.

        Args:
            key: Cache key.

        Returns:
            Cached value if present.
        """
        return None

    def set(self, key: str, value: Any) -> None:
        """Set a cached value by key.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        _ = (key, value)


__all__ = ["DiskCache"]
