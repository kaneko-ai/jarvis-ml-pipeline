"""Cache backend abstractions and a simple in-memory backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheBackend:
    """Minimal cache backend interface used by compatibility tests."""

    _store: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Return value for key or default when absent."""
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store value under key."""
        self._store[key] = value

    def delete(self, key: str) -> bool:
        """Delete key when present and return success."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        """Remove all entries from backend."""
        self._store.clear()


class InMemoryBackend(CacheBackend):
    """Concrete in-memory backend."""
