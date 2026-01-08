import logging
import threading

from jarvis_core.network.degradation import DegradationLevel, get_degradation_manager
from jarvis_core.sync.manager import SyncQueueManager
from jarvis_core.sync.schema import QueueItemStatus

logger = logging.getLogger(__name__)


def on_network_restored(is_online: bool) -> None:
    if not is_online:
        # Update degradation level if needed
        get_degradation_manager().set_level(DegradationLevel.OFFLINE)
        return

    # Network is back
    get_degradation_manager().set_level(DegradationLevel.FULL)
    logger.info("Network restored, starting queue sync...")

    manager = SyncQueueManager()
    status = manager.get_queue_status()

    if status.get(QueueItemStatus.PENDING.value, 0) == 0:
        logger.debug("No pending items to sync")
        return

    # Run in background
    thread = threading.Thread(target=_background_sync, args=(manager,), daemon=True)
    thread.start()


def _background_sync(manager: SyncQueueManager) -> None:
    try:
        results = manager.process_queue(max_items=50)
        completed = sum(1 for r in results if r.status == QueueItemStatus.COMPLETED)
        logger.info(f"Background sync completed: {completed} items processed")
    except Exception as e:
        logger.error(f"Background sync error: {e}")
