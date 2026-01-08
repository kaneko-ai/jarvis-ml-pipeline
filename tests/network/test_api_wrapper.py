from unittest.mock import MagicMock, patch

import pytest

from jarvis_core.network.api_wrapper import (
    OfflineError,
    OfflineQueuedError,
    degradation_aware,
    degradation_aware_with_queue,
)
from jarvis_core.network.degradation import (
    DegradationLevel,
    get_degradation_manager,
)


# Helpers
class MockClient:
    def __init__(self):
        self.cache = {}

    def get_cached_result(self, operation, args, kwargs):
        key = f"{operation}:{args[0]}"
        return self.cache.get(key)

    @degradation_aware
    def fetch_data(self, query):
        return f"Fetched: {query}"

    @degradation_aware_with_queue
    def fetch_data_queue(self, query):
        return f"Fetched: {query}"


@pytest.fixture
def manager():
    mgr = get_degradation_manager()
    mgr.set_level(DegradationLevel.FULL)
    return mgr


def test_degradation_aware_full_mode(manager):
    client = MockClient()
    result = client.fetch_data("test")
    assert result == "Fetched: test"


def test_degradation_aware_offline_no_cache(manager):
    manager.set_level(DegradationLevel.OFFLINE)
    client = MockClient()

    with pytest.raises(OfflineError):
        client.fetch_data("test")


def test_degradation_aware_offline_with_cache(manager):
    manager.set_level(DegradationLevel.OFFLINE)
    client = MockClient()
    client.cache["fetch_data:test"] = "Cached: test"

    result = client.fetch_data("test")
    assert result == "Cached: test"


def test_queue_wrapper_offline_no_cache_no_sync_module(manager):
    # If sync manager import fails (simulated here implicitly effectively if not installed or mocked)
    # But we want to test queueing provided we mock the sync manager.
    manager.set_level(DegradationLevel.OFFLINE)
    client = MockClient()

    # Create a mock module structure
    mock_sync = MagicMock()
    mock_manager_mod = MagicMock()
    mock_queue_cls = MagicMock()
    mock_queue_instance = MagicMock()

    mock_manager_mod.SyncQueueManager = mock_queue_cls
    mock_queue_cls.return_value = mock_queue_instance
    mock_queue_instance.enqueue.return_value = "job-123"

    # Patch sys.modules to simulate the existence of jarvis_core.sync.manager
    with patch.dict(
        "sys.modules", {"jarvis_core.sync": mock_sync, "jarvis_core.sync.manager": mock_manager_mod}
    ):
        with pytest.raises(OfflineQueuedError) as exc:
            client.fetch_data_queue("test")

        assert exc.value.queue_id == "job-123"
        mock_queue_instance.enqueue.assert_called_once()
