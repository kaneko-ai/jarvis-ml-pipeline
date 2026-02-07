"""Cache policy helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CachePolicy:
    """Simple cache policy with TTL semantics."""

    ttl_seconds: int = 3600
    max_items: int = 1000

    def should_cache(self, item_size: int = 1) -> bool:
        """Return whether an item should be cached."""
        if item_size <= 0:
            return False
        return self.max_items > 0 and self.ttl_seconds > 0
