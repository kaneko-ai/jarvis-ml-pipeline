"""JARVIS Network Module.

Network detection and offline mode support.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.5
"""

from jarvis_core.network.detector import (
    NetworkDetector,
    NetworkStatus,
    is_online,
    get_network_status,
)

__all__ = [
    "NetworkDetector",
    "NetworkStatus",
    "is_online",
    "get_network_status",
]
