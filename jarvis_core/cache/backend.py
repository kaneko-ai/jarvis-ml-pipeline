"""Compatibility cache backend module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InMemoryCacheBackend:
    """Simple in-memory cache backend used by compatibility tests."""

    _store: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any | None = None) -> Any | None:
        return self._store.get(key, default)

    def set(self, key: str, value: Any, *_args: Any, **_kwargs: Any) -> None:
        self._store[key] = value

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def clear(self) -> int:
        count = len(self._store)
        self._store.clear()
        return count


CacheBackend = InMemoryCacheBackend
