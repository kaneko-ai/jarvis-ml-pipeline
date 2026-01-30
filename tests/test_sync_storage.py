"""Tests for sync.storage module."""

from datetime import datetime

from jarvis_core.sync.storage import SyncQueueStorage
from jarvis_core.sync.schema import QueueItem, QueueItemStatus


class TestSyncQueueStorage:
    def test_init_with_custom_path(self, tmp_path):
        db_path = tmp_path / "test.db"
        SyncQueueStorage(db_path=db_path)

        assert db_path.exists()

    def test_add_and_get_item(self, tmp_path):
        db_path = tmp_path / "test.db"
        storage = SyncQueueStorage(db_path=db_path)

        item = QueueItem(
            id="test-1",
            operation="search",
            params={"query": "test"},
            status=QueueItemStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        storage.add(item)

        retrieved = storage.get_item("test-1")
        assert retrieved is not None
        assert retrieved.operation == "search"

    def test_add_without_id(self, tmp_path):
        db_path = tmp_path / "test.db"
        storage = SyncQueueStorage(db_path=db_path)

        item = QueueItem(
            id="",  # Empty ID should be auto-generated
            operation="sync",
            params={},
            status=QueueItemStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        storage.add(item)

        # Item should now have an ID
        assert item.id != ""

    def test_get_pending(self, tmp_path):
        db_path = tmp_path / "test.db"
        storage = SyncQueueStorage(db_path=db_path)

        # Add pending items
        for i in range(3):
            item = QueueItem(
                id=f"item-{i}",
                operation="op",
                params={},
                status=QueueItemStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            storage.add(item)

        pending = storage.get_pending(limit=10)
        assert len(pending) == 3

    def test_update_status(self, tmp_path):
        db_path = tmp_path / "test.db"
        storage = SyncQueueStorage(db_path=db_path)

        item = QueueItem(
            id="update-test",
            operation="test",
            params={},
            status=QueueItemStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        storage.add(item)

        storage.update_status("update-test", QueueItemStatus.COMPLETED)

        updated = storage.get_item("update-test")
        assert updated.status == QueueItemStatus.COMPLETED

    def test_update_status_with_error(self, tmp_path):
        db_path = tmp_path / "test.db"
        storage = SyncQueueStorage(db_path=db_path)

        item = QueueItem(
            id="error-test",
            operation="test",
            params={},
            status=QueueItemStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        storage.add(item)

        storage.update_status("error-test", QueueItemStatus.FAILED, error="Test error")

        updated = storage.get_item("error-test")
        assert updated.status == QueueItemStatus.FAILED
        assert updated.error == "Test error"

    def test_get_queue_status(self, tmp_path):
        db_path = tmp_path / "test.db"
        storage = SyncQueueStorage(db_path=db_path)

        # Add items with different statuses
        storage.add(
            QueueItem(
                id="p1",
                operation="op",
                params={},
                status=QueueItemStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )
        storage.add(
            QueueItem(
                id="c1",
                operation="op",
                params={},
                status=QueueItemStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )

        # Update one to completed
        storage.update_status("p1", QueueItemStatus.COMPLETED)

        status = storage.get_queue_status()
        assert isinstance(status, dict)

    def test_get_nonexistent_item(self, tmp_path):
        db_path = tmp_path / "test.db"
        storage = SyncQueueStorage(db_path=db_path)

        result = storage.get_item("nonexistent")
        assert result is None