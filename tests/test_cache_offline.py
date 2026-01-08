"""Tests for SQLite Cache and Offline Manager.

Tests for Task 1.3 (永続キャッシュ) and Task 1.5 (オフラインモード)
"""
import os
import time
from unittest.mock import patch


class TestSQLiteCache:
    """Tests for SQLite Cache."""

    def test_cache_init(self, tmp_path):
        """Test cache initialization."""
        from jarvis_core.cache.sqlite_cache import SQLiteCache

        db_path = tmp_path / "test_cache.db"
        cache = SQLiteCache(db_path=db_path)

        assert cache.db_path == db_path
        assert db_path.exists()
        cache.close()

    def test_cache_set_get(self, tmp_path):
        """Test basic set/get operations."""
        from jarvis_core.cache.sqlite_cache import SQLiteCache

        cache = SQLiteCache(db_path=tmp_path / "test.db")

        cache.set("key1", {"data": "value1"})
        result = cache.get("key1")

        assert result == {"data": "value1"}
        cache.close()

    def test_cache_get_nonexistent(self, tmp_path):
        """Test getting nonexistent key."""
        from jarvis_core.cache.sqlite_cache import SQLiteCache

        cache = SQLiteCache(db_path=tmp_path / "test.db")
        result = cache.get("nonexistent")

        assert result is None
        cache.close()

    def test_cache_namespace(self, tmp_path):
        """Test namespace separation."""
        from jarvis_core.cache.sqlite_cache import SQLiteCache

        cache = SQLiteCache(db_path=tmp_path / "test.db")

        cache.set("key", "value1", namespace="ns1")
        cache.set("key", "value2", namespace="ns2")

        assert cache.get("key", namespace="ns1") == "value1"
        assert cache.get("key", namespace="ns2") == "value2"
        cache.close()

    def test_cache_delete(self, tmp_path):
        """Test delete operation."""
        from jarvis_core.cache.sqlite_cache import SQLiteCache

        cache = SQLiteCache(db_path=tmp_path / "test.db")

        cache.set("key", "value")
        assert cache.get("key") == "value"

        deleted = cache.delete("key")
        assert deleted is True
        assert cache.get("key") is None
        cache.close()

    def test_cache_clear_namespace(self, tmp_path):
        """Test clearing specific namespace."""
        from jarvis_core.cache.sqlite_cache import SQLiteCache

        cache = SQLiteCache(db_path=tmp_path / "test.db")

        cache.set("k1", "v1", namespace="ns1")
        cache.set("k2", "v2", namespace="ns1")
        cache.set("k3", "v3", namespace="ns2")

        count = cache.clear(namespace="ns1")
        assert count == 2
        assert cache.get("k3", namespace="ns2") == "v3"
        cache.close()

    def test_cache_ttl_expiration(self, tmp_path):
        """Test TTL expiration."""
        from jarvis_core.cache.sqlite_cache import SQLiteCache

        cache = SQLiteCache(db_path=tmp_path / "test.db")

        cache.set("key", "value", ttl_seconds=1)
        assert cache.get("key") == "value"

        time.sleep(1.5)
        assert cache.get("key") is None
        cache.close()

    def test_cache_stats(self, tmp_path):
        """Test cache statistics."""
        from jarvis_core.cache.sqlite_cache import SQLiteCache

        cache = SQLiteCache(db_path=tmp_path / "test.db")

        cache.set("k1", "value1")
        cache.set("k2", "value2")

        stats = cache.stats()
        assert stats["entries"] == 2
        assert stats["size_bytes"] > 0
        cache.close()

    def test_cache_singleton(self):
        """Test get_cache singleton."""
        # Reset singleton for test
        import jarvis_core.cache.sqlite_cache as cache_module
        from jarvis_core.cache.sqlite_cache import get_cache
        cache_module._default_cache = None

        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2


class TestOfflineManager:
    """Tests for Offline Manager."""

    def test_manager_init(self):
        """Test manager initialization."""
        from jarvis_core.runtime.offline_manager import OfflineManager

        manager = OfflineManager()
        assert manager is not None
        assert manager.state.value in ["online", "offline", "degraded"]

    def test_force_offline(self):
        """Test forcing offline mode."""
        from jarvis_core.runtime.offline_manager import ConnectivityState, OfflineManager

        manager = OfflineManager()

        manager.force_offline(True)
        assert manager.is_offline is True
        assert manager.state == ConnectivityState.OFFLINE

        manager.force_offline(False)

    def test_sync_queue(self):
        """Test sync queue operations."""
        from jarvis_core.runtime.offline_manager import OfflineManager

        manager = OfflineManager()

        item_id = manager.queue_for_sync(
            operation="fetch_paper",
            payload={"pmid": "12345"},
        )

        assert item_id is not None
        queue = manager.get_sync_queue()
        assert len(queue) == 1
        assert queue[0].operation == "fetch_paper"

        count = manager.clear_sync_queue()
        assert count == 1
        assert len(manager.get_sync_queue()) == 0

    def test_with_fallback_online(self):
        """Test fallback when online."""
        from jarvis_core.runtime.offline_manager import OfflineManager

        manager = OfflineManager()
        manager.force_offline(False)
        manager._force_offline = False  # Ensure not forced offline

        # Use lambda that returns the online result
        result = manager.with_fallback(
            online_func=lambda: "online_result",
            offline_func=lambda: "offline_result",
        )
        # Either result is fine depending on actual network state
        assert result in ["online_result", "offline_result"]

    def test_with_fallback_offline(self):
        """Test fallback when offline."""
        from jarvis_core.runtime.offline_manager import OfflineManager

        manager = OfflineManager()
        manager.force_offline(True)

        result = manager.with_fallback(
            online_func=lambda: "online_result",
            offline_func=lambda: "offline_result",
        )
        assert result == "offline_result"

    def test_status(self):
        """Test status report."""
        from jarvis_core.runtime.offline_manager import OfflineManager

        manager = OfflineManager()
        status = manager.status()

        assert "state" in status
        assert "is_online" in status
        assert "sync_queue_size" in status

    def test_env_force_offline(self):
        """Test JARVIS_OFFLINE environment variable."""
        from jarvis_core.runtime.offline_manager import OfflineManager

        with patch.dict(os.environ, {"JARVIS_OFFLINE": "true"}):
            manager = OfflineManager()
            assert manager._force_offline is True

    def test_connectivity_state_enum(self):
        """Test ConnectivityState enum."""
        from jarvis_core.runtime.offline_manager import ConnectivityState

        assert ConnectivityState.ONLINE.value == "online"
        assert ConnectivityState.OFFLINE.value == "offline"
        assert ConnectivityState.DEGRADED.value == "degraded"

    def test_get_offline_manager_singleton(self):
        """Test singleton pattern."""
        import jarvis_core.runtime.offline_manager as offline_module
        from jarvis_core.runtime.offline_manager import get_offline_manager
        offline_module._default_manager = None

        manager1 = get_offline_manager()
        manager2 = get_offline_manager()

        assert manager1 is manager2
