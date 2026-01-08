import logging
import uuid
from collections.abc import Callable
from typing import Any

from jarvis_core.sync.schema import QueueItem, QueueItemStatus
from jarvis_core.sync.storage import SyncQueueStorage

logger = logging.getLogger(__name__)


class SyncQueueManager:
    def __init__(self):
        self.storage = SyncQueueStorage()
        self._handlers: dict[str, Callable] = {}

        # Auto-register default handlers?
        # Ideally this is done explicitly via registration or a separate setup.
        # But instructions say "Task 1.5.3: Default Handler Registration -> handlers.py"
        # So we keep it separate or import it here if needed.
        from jarvis_core.sync.handlers import register_default_handlers

        register_default_handlers(self)

    def register_handler(self, operation: str, handler: Callable) -> None:
        self._handlers[operation] = handler

    def enqueue(self, operation: str, params: dict[str, Any]) -> str:
        # Deduplication could be here
        item = QueueItem(
            id=str(uuid.uuid4()),
            operation=operation,
            params=params,
        )
        self.storage.add(item)
        return item.id

    def process_queue(self, max_items: int = 10) -> list[QueueItem]:
        pending = self.storage.get_pending(limit=max_items)
        results = []

        for item in pending:
            handler = self._handlers.get(item.operation)
            if not handler:
                self.storage.update_status(item.id, QueueItemStatus.FAILED, "No handler")
                item.status = QueueItemStatus.FAILED
                item.error = "No handler"
                results.append(item)
                continue

            try:
                self.storage.update_status(item.id, QueueItemStatus.IN_PROGRESS)

                # Handler signature: we expect it to take **params
                # But params is a dict.
                if "args" in item.params and "kwargs" in item.params:
                    # Special case for general function wrapping
                    args = item.params["args"]
                    kwargs = item.params["kwargs"]
                    handler(*args, **kwargs)
                else:
                    handler(**item.params)

                self.storage.update_status(item.id, QueueItemStatus.COMPLETED)
                item.status = QueueItemStatus.COMPLETED
            except Exception as e:
                logger.error(f"Sync failed for {item.id}: {e}", exc_info=True)
                self.storage.update_status(item.id, QueueItemStatus.FAILED, str(e))
                item.status = QueueItemStatus.FAILED
                item.error = str(e)

            results.append(item)

        return results

    def get_queue_status(self) -> dict[str, int]:
        return self.storage.get_queue_status()
