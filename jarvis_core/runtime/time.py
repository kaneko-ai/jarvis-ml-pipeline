"""Deterministic Time.

Per PR-66, provides freezable time for reproducibility.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import threading


_frozen_time: Optional[datetime] = None
_lock = threading.Lock()


def freeze_time(dt: datetime) -> None:
    """Freeze time to a specific datetime."""
    global _frozen_time
    with _lock:
        _frozen_time = dt


def unfreeze_time() -> None:
    """Unfreeze time (return to real time)."""
    global _frozen_time
    with _lock:
        _frozen_time = None


def now() -> datetime:
    """Get current time (frozen if set, otherwise real)."""
    with _lock:
        if _frozen_time is not None:
            return _frozen_time
    return datetime.now(timezone.utc)


def now_iso() -> str:
    """Get current time as ISO string."""
    return now().isoformat()


class FrozenTime:
    """Context manager for freezing time."""

    def __init__(self, dt: datetime):
        self.dt = dt
        self._previous: Optional[datetime] = None

    def __enter__(self):
        global _frozen_time
        with _lock:
            self._previous = _frozen_time
            _frozen_time = self.dt
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _frozen_time
        with _lock:
            _frozen_time = self._previous
        return False


def frozen_time(dt: Optional[datetime] = None) -> FrozenTime:
    """Create a frozen time context.

    Usage:
        with frozen_time(datetime(2024, 1, 1)):
            assert now().year == 2024
    """
    if dt is None:
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return FrozenTime(dt)
