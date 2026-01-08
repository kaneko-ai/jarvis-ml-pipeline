from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# Try to import is_online safely to avoid circular imports if possible,
# or import it inside the method.

class DegradationLevel(Enum):
    FULL = "full"           # All features available
    LIMITED = "limited"     # External APIs disabled, local cache only
    OFFLINE = "offline"     # Completely offline
    CRITICAL = "critical"   # No cache available

@dataclass
class DegradationManager:
    _current_level: DegradationLevel = DegradationLevel.FULL
    _listeners: list[Callable[[DegradationLevel, DegradationLevel], None]] = field(default_factory=list)

    _instance: Optional['DegradationManager'] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_level(self) -> DegradationLevel:
        return self._current_level

    def set_level(self, level: DegradationLevel) -> None:
        old_level = self._current_level
        self._current_level = level
        if old_level != level:
            self._notify_listeners(old_level, level)

    def add_listener(self, callback: Callable[[DegradationLevel, DegradationLevel], None]) -> None:
        self._listeners.append(callback)

    def _notify_listeners(self, old: DegradationLevel, new: DegradationLevel) -> None:
        for listener in self._listeners:
            try:
                listener(old, new)
            except Exception:
                # Log error but don't stop notification
                pass

    def auto_detect_level(self) -> DegradationLevel:
        from jarvis_core.network.detector import is_online

        # Simple check for now, can be expanded
        if is_online():
            return DegradationLevel.FULL

        # Check cache availability (mock for now, should import cache manager)
        try:
            # from jarvis_core.cache import MultiLevelCache
            # cache = MultiLevelCache()
            # if cache.get_stats().total_entries > 0:
            #     return DegradationLevel.LIMITED
            pass
        except ImportError:
            pass

        # Default to LIMITED if offline but not CRITICAL
        # If we can verify cache is empty/broken, return CRITICAL
        return DegradationLevel.OFFLINE

def get_degradation_manager() -> DegradationManager:
    return DegradationManager.get_instance()
