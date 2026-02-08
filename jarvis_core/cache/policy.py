"""Compatibility cache policy module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CachePolicy:
    """Minimal cache policy used by legacy tests."""

    enabled: bool = True
    default_ttl_seconds: int = 3600

    def should_cache(self, _key: str, *_args: object, **_kwargs: object) -> bool:
        return self.enabled

    def ttl_for(self, _key: str, *_args: object, **_kwargs: object) -> int:
        return self.default_ttl_seconds
