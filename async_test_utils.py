from __future__ import annotations

import asyncio
import threading
from functools import wraps
from typing import TypeVar

T = TypeVar("T")


def run_async(awaitable):
    """Run an awaitable safely from sync tests, even if a loop is already running."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    state: dict[str, object] = {"result": None, "error": None}

    def _runner() -> None:
        try:
            state["result"] = asyncio.run(awaitable)
        except BaseException as exc:  # pragma: no cover - re-raised in caller thread
            state["error"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()

    error = state["error"]
    if error is not None:
        raise error
    return state["result"]


def sync_async_test(func):
    """Decorator to run async pytest tests as sync tests."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return run_async(func(*args, **kwargs))

    return wrapper
