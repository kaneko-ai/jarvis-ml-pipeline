"""Tests for sync module - Coverage improvement (FIXED)."""

import pytest
from unittest.mock import Mock, patch


class TestSyncQueueManager:
    """Tests for SyncQueueManager class."""

    def test_sync_queue_manager_creation(self):
        """Test SyncQueueManager creation."""
        from jarvis_core.sync.manager import SyncQueueManager

        manager = SyncQueueManager()
        assert manager is not None
        assert manager.storage is not None

    def test_enqueue(self):
        """Test enqueueing operation."""
        from jarvis_core.sync.manager import SyncQueueManager

        manager = SyncQueueManager()
        queue_id = manager.enqueue(
            operation="test_op",
            params={"key": "value"},
        )
        assert queue_id is not None
        assert isinstance(queue_id, str)

    def test_register_handler(self):
        """Test registering a handler."""
        from jarvis_core.sync.manager import SyncQueueManager

        manager = SyncQueueManager()
        handler = Mock()

        manager.register_handler("custom_op", handler)

        assert "custom_op" in manager._handlers

    def test_get_queue_status(self):
        """Test getting queue status."""
        from jarvis_core.sync.manager import SyncQueueManager

        manager = SyncQueueManager()
        status = manager.get_queue_status()

        assert isinstance(status, dict)

    def test_process_queue_no_handler(self):
        """Test processing queue with no handler."""
        from jarvis_core.sync.manager import SyncQueueManager

        manager = SyncQueueManager()
        manager._handlers = {}  # Clear handlers
        manager.enqueue("unknown_op", {})

        results = manager.process_queue(max_items=1)
        # Should return results even if handler missing


class TestSyncSchema:
    """Tests for sync schema module."""

    def test_queue_item_creation(self):
        """Test QueueItem creation."""
        from jarvis_core.sync.schema import QueueItem

        item = QueueItem(
            id="test-id",
            operation="search",
            params={"query": "test"},
        )

        assert item.id == "test-id"
        assert item.operation == "search"

    def test_queue_item_status_enum(self):
        """Test QueueItemStatus enum."""
        from jarvis_core.sync.schema import QueueItemStatus

        assert QueueItemStatus.PENDING.value == "pending"
        assert QueueItemStatus.COMPLETED.value == "completed"
        assert QueueItemStatus.FAILED.value == "failed"


class TestSyncProgress:
    """Tests for sync progress module."""

    def test_progress_import(self):
        """Test progress module import."""
        from jarvis_core.sync import progress

        assert progress is not None


class TestModuleImports:
    """Test module imports."""

    def test_sync_imports(self):
        """Test sync module imports."""
        from jarvis_core.sync import (
            manager,
            handlers,
        )

        assert manager is not None
        assert handlers is not None
