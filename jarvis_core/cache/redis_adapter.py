"""Redis cache adapter stub."""

from __future__ import annotations

from typing import Any


class RedisCache:
    """Minimal Redis cache adapter."""

    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        """Initialize the adapter.

        Args:
            url: Redis connection URL.
        """
        self.url = url

    def get(self, key: str) -> Any | None:
        """Get a cached value by key.

        Args:
            key: Cache key.

        Returns:
            Cached value if present.
        """
        _ = key
        return None

    def set(self, key: str, value: Any) -> None:
        """Set a cached value by key.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        _ = (key, value)


__all__ = ["RedisCache"]
