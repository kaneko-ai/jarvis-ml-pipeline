from unittest.mock import MagicMock, patch

from jarvis_core.sync.manager import SyncQueueManager
from jarvis_core.sync.schema import QueueItem, QueueItemStatus
from jarvis_core.sync.storage import SyncQueueStorage


def test_queue_item_creation():
    item = QueueItem(id="1", operation="test", params={"a": 1})
    assert item.status == QueueItemStatus.PENDING
    assert item.to_dict()["params"] == {"a": 1}

def test_storage_add_and_get(tmp_path):
    # Use tmp file for testing
    db_path = tmp_path / "test_queue.db"
    storage = SyncQueueStorage(db_path=db_path)
    item = QueueItem(id="1", operation="test", params={"a": 1})
    storage.add(item)

    pending = storage.get_pending()
    assert len(pending) == 1
    assert pending[0].id == "1"

def test_manager_process_queue():
    # Patch the class in the manager module where it is imported
    with patch('jarvis_core.sync.manager.SyncQueueStorage') as mock_storage_cls:
        mock_storage = MagicMock()
        mock_storage_cls.return_value = mock_storage

        item = QueueItem(id="1", operation="search", params={"query": "test"})
        mock_storage.get_pending.return_value = [item]

        manager = SyncQueueManager()
        # Mock handler
        mock_handler = MagicMock()
        manager.register_handler("search", mock_handler)

        results = manager.process_queue()

        assert len(results) == 1
        assert results[0].status == QueueItemStatus.COMPLETED
        mock_handler.assert_called_once()
        mock_storage.update_status.assert_called()

def test_manager_process_queue_no_handler():
     # Patch the class in the manager module where it is imported
     with patch('jarvis_core.sync.manager.SyncQueueStorage') as mock_storage_cls:
        mock_storage = MagicMock()
        mock_storage_cls.return_value = mock_storage

        item = QueueItem(id="1", operation="unknown", params={})
        mock_storage.get_pending.return_value = [item]

        manager = SyncQueueManager()
        results = manager.process_queue()

        assert len(results) == 1
        assert results[0].status == QueueItemStatus.FAILED
