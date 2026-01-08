import functools
from collections.abc import Callable
from typing import Any

from jarvis_core.network.degradation import DegradationLevel, get_degradation_manager


class OfflineError(Exception):
    """Raised when an operation cannot be performed in offline mode."""

    pass


class OfflineQueuedError(Exception):
    """Raised when an operation is queued for later execution."""

    def __init__(self, message: str, queue_id: str):
        super().__init__(message)
        self.queue_id = queue_id


def degradation_aware(func: Callable) -> Callable:
    """Decorator to handle offline mode by attempting cache fallback or raising OfflineError."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        manager = get_degradation_manager()
        level = manager.get_level()

        if level in (DegradationLevel.LIMITED, DegradationLevel.OFFLINE, DegradationLevel.CRITICAL):
            # Try to get from cache if the object supports it
            # Assumes the first argument is 'self' and has a 'cache' or similar mechanism
            # or usage of a global cache.

            # For now, we will assume the method might have its own cache logic if connected,
            # but if we are strictly offline, we should try a "only cache" approach if possible.
            # However, usually the client itself handles "search" by calling an external API.

            # If we can't make the request, we should try to return cached result.
            # This requires a standardized way to key the request.
            # For this MVP, we will assume if the function raises an error or we check level first,
            # we try to see if we can "get_cached"

            # Simple implementation: fail if offline
            # The instruction says: "Cache fallback"
            # We need a way to access cache.

            # Assuming the instance (self) has local_search or similar if it's a UnifiedSourceClient
            # Or we standardize that arguments can be hashed.

            # For now, simply raise an error if we can't find a smart way,
            # OR better: The user instruction implies specific logic:
            # "cache_key = compute_cache_key... returned cached"

            # We'll rely on the object having a 'get_from_cache' method or similar,
            # or try to calculate a generic key.

            try:
                # Try simple cache lookup if available on self
                if args and hasattr(args[0], "get_cached_result"):
                    res = args[0].get_cached_result(func.__name__, args[1:], kwargs)
                    if res is not None:
                        return res
            except Exception:
                pass

            raise OfflineError(f"Offline mode: {func.__name__} unavailable")

        return func(*args, **kwargs)

    return wrapper


def degradation_aware_with_queue(func: Callable) -> Callable:
    """Decorator: Offline -> Check Cache -> Queue if missing."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        manager = get_degradation_manager()
        level = manager.get_level()

        if level in (DegradationLevel.LIMITED, DegradationLevel.OFFLINE):
            # 1. Try Cache
            try:
                if args and hasattr(args[0], "get_cached_result"):
                    res = args[0].get_cached_result(func.__name__, args[1:], kwargs)
                    if res is not None:
                        return res
            except Exception:
                pass

            # 2. Queue
            # We need to import SyncQueueManager here to avoid circular imports at top level
            try:
                from jarvis_core.sync.manager import SyncQueueManager

                queue_manager = SyncQueueManager()
                # Serialize args/kwargs needs care, but for basic types it's ok.
                # args[0] is 'self', we shouldn't queue 'self'.

                # Construct params
                # We need a way to reconstruct the call.
                # Usually we register a handler string.

                queue_id = queue_manager.enqueue(
                    operation=func.__name__,  # Or some registry key
                    params={"args": args[1:], "kwargs": kwargs},  # Skip self
                )
                raise OfflineQueuedError(f"Queued for sync: {queue_id}", queue_id)
            except ImportError:
                # If sync module not ready, just raise OfflineError
                raise OfflineError("Offline and sync manager unavailable")

        return func(*args, **kwargs)

    return wrapper
