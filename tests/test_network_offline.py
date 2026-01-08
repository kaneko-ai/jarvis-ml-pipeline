"""Tests for the Network/Offline Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 1.5
"""

from unittest.mock import Mock, patch

import pytest


class TestNetworkDetector:
    """Tests for NetworkDetector."""

    def test_detector_initialization(self):
        """Test NetworkDetector initialization."""
        from jarvis_core.network import NetworkDetector

        detector = NetworkDetector()
        assert detector is not None

    def test_is_online_when_connected(self):
        """Test is_online returns True when connected."""
        from jarvis_core.network import NetworkDetector

        detector = NetworkDetector()

        with patch("socket.create_connection") as mock_conn:
            mock_conn.return_value = Mock()

            result = detector.is_online()

            assert result is True

    def test_is_online_when_disconnected(self):
        """Test is_online returns False when disconnected."""

        from jarvis_core.network import NetworkDetector

        detector = NetworkDetector()

        with patch("socket.create_connection") as mock_conn:
            mock_conn.side_effect = TimeoutError()

            result = detector.is_online()

            assert result is False

    def test_get_network_status(self):
        """Test get_network_status returns NetworkStatus."""
        from jarvis_core.network import NetworkDetector, NetworkStatus

        detector = NetworkDetector()

        status = detector.get_status()

        assert isinstance(status, NetworkStatus)
        assert hasattr(status, "is_online")
        assert hasattr(status, "latency_ms")


class TestNetworkStatus:
    """Tests for NetworkStatus dataclass."""

    def test_status_creation(self):
        """Test NetworkStatus creation."""
        from jarvis_core.network import NetworkStatus

        status = NetworkStatus(
            is_online=True,
            latency_ms=50.0,
            last_check=1704067200.0,
        )

        assert status.is_online is True
        assert status.latency_ms == 50.0

    def test_status_offline(self):
        """Test NetworkStatus for offline state."""
        from jarvis_core.network import NetworkStatus

        status = NetworkStatus(
            is_online=False,
            latency_ms=None,
            last_check=1704067200.0,
        )

        assert status.is_online is False
        assert status.latency_ms is None


class TestDegradationLevel:
    """Tests for DegradationLevel enum."""

    def test_degradation_levels(self):
        """Test DegradationLevel enum values."""
        from jarvis_core.network import DegradationLevel

        assert DegradationLevel.FULL.value == "full"
        assert DegradationLevel.DEGRADED.value == "degraded"
        assert DegradationLevel.OFFLINE.value == "offline"


class TestDegradationManager:
    """Tests for DegradationManager."""

    def test_manager_initialization(self):
        """Test DegradationManager initialization."""
        from jarvis_core.network import DegradationManager

        manager = DegradationManager()
        assert manager is not None

    def test_get_current_level_online(self):
        """Test get_current_level when online."""
        from jarvis_core.network import DegradationLevel, DegradationManager

        manager = DegradationManager()

        with patch.object(manager, "_check_network", return_value=True):
            level = manager.get_current_level()

            assert level == DegradationLevel.FULL

    def test_get_current_level_offline(self):
        """Test get_current_level when offline."""
        from jarvis_core.network import DegradationLevel, DegradationManager

        manager = DegradationManager()

        with patch.object(manager, "_check_network", return_value=False):
            level = manager.get_current_level()

            assert level == DegradationLevel.OFFLINE

    def test_feature_availability_online(self):
        """Test feature availability when online."""
        from jarvis_core.network import DegradationLevel, DegradationManager

        manager = DegradationManager()
        manager._current_level = DegradationLevel.FULL

        assert manager.is_feature_available("api_search") is True
        assert manager.is_feature_available("local_search") is True

    def test_feature_availability_offline(self):
        """Test feature availability when offline."""
        from jarvis_core.network import DegradationLevel, DegradationManager

        manager = DegradationManager()
        manager._current_level = DegradationLevel.OFFLINE

        assert manager.is_feature_available("api_search") is False
        assert manager.is_feature_available("local_search") is True


class TestDegradationAwareDecorator:
    """Tests for degradation_aware decorator."""

    def test_decorator_online(self):
        """Test decorator when online."""
        from jarvis_core.network import degradation_aware

        @degradation_aware(feature="api_search")
        def fetch_from_api():
            return "api_result"

        with patch("jarvis_core.network.get_degradation_manager") as mock_mgr:
            mock_mgr.return_value.is_feature_available.return_value = True

            result = fetch_from_api()

            assert result == "api_result"

    def test_decorator_offline_raises(self):
        """Test decorator raises OfflineError when offline."""
        from jarvis_core.network import OfflineError, degradation_aware

        @degradation_aware(feature="api_search")
        def fetch_from_api():
            return "api_result"

        with patch("jarvis_core.network.get_degradation_manager") as mock_mgr:
            mock_mgr.return_value.is_feature_available.return_value = False

            with pytest.raises(OfflineError):
                fetch_from_api()

    def test_decorator_with_fallback(self):
        """Test decorator with fallback function."""
        from jarvis_core.network import degradation_aware

        def fallback_func():
            return "fallback_result"

        @degradation_aware(feature="api_search", fallback=fallback_func)
        def fetch_from_api():
            return "api_result"

        with patch("jarvis_core.network.get_degradation_manager") as mock_mgr:
            mock_mgr.return_value.is_feature_available.return_value = False

            result = fetch_from_api()

            assert result == "fallback_result"


class TestDegradationAwareWithQueue:
    """Tests for degradation_aware_with_queue decorator."""

    def test_queue_decorator_online(self):
        """Test queue decorator when online."""
        from jarvis_core.network import degradation_aware_with_queue

        @degradation_aware_with_queue(feature="api_sync")
        def sync_data(data):
            return f"synced:{data}"

        with patch("jarvis_core.network.get_degradation_manager") as mock_mgr:
            mock_mgr.return_value.is_feature_available.return_value = True

            result = sync_data("test")

            assert result == "synced:test"

    def test_queue_decorator_offline_queues(self):
        """Test queue decorator queues operation when offline."""
        from jarvis_core.network import OfflineQueuedError, degradation_aware_with_queue

        @degradation_aware_with_queue(feature="api_sync")
        def sync_data(data):
            return f"synced:{data}"

        with patch("jarvis_core.network.get_degradation_manager") as mock_mgr:
            mock_mgr.return_value.is_feature_available.return_value = False

            with pytest.raises(OfflineQueuedError) as exc_info:
                sync_data("test")

            assert exc_info.value.queued is True


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_is_online_function(self):
        """Test is_online convenience function."""
        from jarvis_core.network import is_online

        result = is_online()

        assert isinstance(result, bool)

    def test_get_network_status_function(self):
        """Test get_network_status convenience function."""
        from jarvis_core.network import NetworkStatus, get_network_status

        status = get_network_status()

        assert isinstance(status, NetworkStatus)

    def test_get_degradation_manager_function(self):
        """Test get_degradation_manager convenience function."""
        from jarvis_core.network import DegradationManager, get_degradation_manager

        manager = get_degradation_manager()

        assert isinstance(manager, DegradationManager)

    def test_get_degradation_manager_singleton(self):
        """Test get_degradation_manager returns singleton."""
        from jarvis_core.network import get_degradation_manager

        manager1 = get_degradation_manager()
        manager2 = get_degradation_manager()

        assert manager1 is manager2


class TestOfflineErrors:
    """Tests for offline error classes."""

    def test_offline_error(self):
        """Test OfflineError exception."""
        from jarvis_core.network import OfflineError

        error = OfflineError("Feature unavailable offline")

        assert str(error) == "Feature unavailable offline"
        assert isinstance(error, Exception)

    def test_offline_queued_error(self):
        """Test OfflineQueuedError exception."""
        from jarvis_core.network import OfflineQueuedError

        error = OfflineQueuedError("Operation queued", queue_id="q123")

        assert error.queued is True
        assert error.queue_id == "q123"


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.network import (
            DegradationLevel,
            DegradationManager,
            NetworkDetector,
            NetworkStatus,
            is_online,
        )

        assert NetworkDetector is not None
        assert NetworkStatus is not None
        assert is_online is not None
        assert DegradationLevel is not None
        assert DegradationManager is not None
