"""
JARVIS Hindsight Memory Module

World / Experience / Observation / Opinion の分離
"""

from .hindsight import (
    HindsightMemory,
    MemoryEntry,
    MemoryType,
)

# TODO(deprecate): Backwards compatibility re-exports from memory_utils
try:
    from jarvis_core.memory_utils import find_related, get_memory_stats, search_memory
except ImportError:
    search_memory = None
    find_related = None
    get_memory_stats = None

__all__ = [
    "MemoryType",
    "MemoryEntry",
    "HindsightMemory",
    "search_memory",
    "find_related",
    "get_memory_stats",
]