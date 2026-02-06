"""Profiling helpers for development."""

from __future__ import annotations

import time


class Profiler:
    """Simple wall-clock profiler."""

    def __init__(self) -> None:
        """Initialize profiler."""
        self._start: float | None = None
        self._elapsed: float = 0.0

    def start(self) -> None:
        """Start timing."""
        self._start = time.perf_counter()

    def stop(self) -> None:
        """Stop timing and accumulate elapsed time."""
        if self._start is None:
            return
        self._elapsed += time.perf_counter() - self._start
        self._start = None

    def report(self) -> dict[str, float]:
        """Return timing report.

        Returns:
            Dict with elapsed seconds.
        """
        return {"elapsed_seconds": self._elapsed}


__all__ = ["Profiler"]
