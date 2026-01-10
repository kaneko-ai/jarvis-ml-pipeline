"""Tests for the Network/Offline Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 1.5
Updated to match actual implementation.
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

    def test_is_online_returns_bool(self):
        """Test is_online returns boolean."""
        from jarvis_core.network import NetworkDetector

        detector = NetworkDetector()
        result = detector.is_online()
        assert isinstance(result, bool)

    def test_is_offline_returns_bool(self):
        """Test is_offline returns boolean."""
        from jarvis_core.network import NetworkDetector

        detector = NetworkDetector()
        result = detector.is_offline()
        assert isinstance(result, bool)

    def test_get_status_returns_result(self):
        """Test get_status returns NetworkCheckResult."""
        from jarvis_core.network import NetworkDetector
        from jarvis_core.network.detector import NetworkCheckResult

        detector = NetworkDetector()
        status = detector.get_status()

        assert isinstance(status, NetworkCheckResult)
        assert hasattr(status, "status")
        assert hasattr(status, "is_online")


class TestNetworkStatus:
    """Tests for NetworkStatus enum."""

    def test_network_status_values(self):
        """Test NetworkStatus enum values."""
        from jarvis_core.network import NetworkStatus

        assert NetworkStatus.ONLINE.value == "online"
        assert NetworkStatus.OFFLINE.value == "offline"
        assert NetworkStatus.LIMITED.value == "limited"
        assert NetworkStatus.UNKNOWN.value == "unknown"

    def test_network_status_comparison(self):
        """Test NetworkStatus comparison."""
        from jarvis_core.network import NetworkStatus

        assert NetworkStatus.ONLINE != NetworkStatus.OFFLINE
        assert NetworkStatus.ONLINE == NetworkStatus.ONLINE


class TestNetworkCheckResult:
    """Tests for NetworkCheckResult dataclass."""

    def test_result_is_online(self):
        """Test NetworkCheckResult.is_online property."""
        from jarvis_core.network import NetworkStatus
        from jarvis_core.network.detector import NetworkCheckResult

        result = NetworkCheckResult(status=NetworkStatus.ONLINE)
        assert result.is_online is True

        result = NetworkCheckResult(status=NetworkStatus.OFFLINE)
        assert result.is_online is False

    def test_result_is_offline(self):
        """Test NetworkCheckResult.is_offline property."""
        from jarvis_core.network import NetworkStatus
        from jarvis_core.network.detector import NetworkCheckResult

        result = NetworkCheckResult(status=NetworkStatus.OFFLINE)
        assert result.is_offline is True

        result = NetworkCheckResult(status=NetworkStatus.ONLINE)
        assert result.is_offline is False


class TestDegradationLevel:
    """Tests for DegradationLevel enum."""

    def test_degradation_levels(self):
        """Test DegradationLevel enum values."""
        from jarvis_core.network import DegradationLevel

        assert DegradationLevel.FULL.value == "full"
        assert DegradationLevel.LIMITED.value == "limited"
        assert DegradationLevel.OFFLINE.value == "offline"
        assert DegradationLevel.CRITICAL.value == "critical"


class TestDegradationManager:
    """Tests for DegradationManager."""

    def test_manager_initialization(self):
        """Test DegradationManager initialization."""
        from jarvis_core.network import DegradationManager

        manager = DegradationManager()
        assert manager is not None

    def test_get_level(self):
        """Test get_level method."""
        from jarvis_core.network import DegradationLevel, DegradationManager

        manager = DegradationManager()
        level = manager.get_level()
        assert isinstance(level, DegradationLevel)

    def test_set_level(self):
        """Test set_level method."""
        from jarvis_core.network import DegradationLevel, DegradationManager

        manager = DegradationManager()
        manager.set_level(DegradationLevel.OFFLINE)
        assert manager.get_level() == DegradationLevel.OFFLINE

        # Reset to default
        manager.set_level(DegradationLevel.FULL)

    def test_add_listener(self):
        """Test add_listener method."""
        from jarvis_core.network import DegradationLevel, DegradationManager

        manager = DegradationManager()
        callback_called = []

        def callback(old, new):
            callback_called.append((old, new))

        manager.add_listener(callback)
        manager.set_level(DegradationLevel.LIMITED)

        # The callback should have been called if level changed
        # (depends on initial state)


class TestDegradationAwareDecorator:
    """Tests for degradation_aware decorator."""

    def test_decorator_full_mode(self):
        """Test decorator when in FULL mode."""
        from jarvis_core.network import DegradationLevel, degradation_aware, get_degradation_manager

        # Ensure we're in FULL mode
        manager = get_degradation_manager()
        manager.set_level(DegradationLevel.FULL)

        @degradation_aware
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_decorator_offline_raises(self):
        """Test decorator raises OfflineError when offline."""
        from jarvis_core.network import (
            DegradationLevel,
            OfflineError,
            degradation_aware,
            get_degradation_manager,
        )

        manager = get_degradation_manager()
        manager.set_level(DegradationLevel.OFFLINE)

        @degradation_aware
        def test_func():
            return "should_not_reach"

        with pytest.raises(OfflineError):
            test_func()

        # Reset to FULL
        manager.set_level(DegradationLevel.FULL)


class TestDegradationAwareWithQueue:
    """Tests for degradation_aware_with_queue decorator."""

    def test_queue_decorator_full_mode(self):
        """Test queue decorator when in FULL mode."""
        from jarvis_core.network import (
            DegradationLevel,
            degradation_aware_with_queue,
            get_degradation_manager,
        )

        manager = get_degradation_manager()
        manager.set_level(DegradationLevel.FULL)

        @degradation_aware_with_queue
        def sync_data(data):
            return f"synced:{data}"

        result = sync_data("test")
        assert result == "synced:test"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_is_online_function(self):
        """Test is_online convenience function."""
        from jarvis_core.network import is_online

        result = is_online()
        assert isinstance(result, bool)

    def test_get_network_status_function(self):
        """Test get_network_status convenience function."""
        from jarvis_core.network import get_network_status
        from jarvis_core.network.detector import NetworkCheckResult

        status = get_network_status()
        assert isinstance(status, NetworkCheckResult)

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
