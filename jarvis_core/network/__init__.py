"""JARVIS Network Module.

Network detection and offline mode support.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.5
"""

from jarvis_core.network.detector import (
    NetworkDetector,
    NetworkStatus,
    get_network_status,
    is_online,
)

__all__ = [
    "NetworkDetector",
    "NetworkStatus",
    "is_online",
    "get_network_status",
    "DegradationLevel",
    "DegradationManager",
    "get_degradation_manager",
    "degradation_aware",
    "degradation_aware_with_queue",
    "OfflineError",
    "OfflineQueuedError",
]

from jarvis_core.network.api_wrapper import (
    OfflineError,
    OfflineQueuedError,
    degradation_aware,
    degradation_aware_with_queue,
)
from jarvis_core.network.degradation import (
    DegradationLevel,
    DegradationManager,
    get_degradation_manager,
)