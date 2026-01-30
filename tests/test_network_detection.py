"""Tests for Network Detection Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 1.5
Comprehensive test suite for network detection functionality.
"""

from unittest.mock import Mock, patch, MagicMock
import socket
import time
from datetime import datetime


class TestNetworkStatus:
    """Tests for NetworkStatus enum."""

    def test_enum_values(self):
        """Test NetworkStatus enum values."""
        from jarvis_core.network.detector import NetworkStatus

        assert NetworkStatus.ONLINE.value == "online"
        assert NetworkStatus.OFFLINE.value == "offline"
        assert NetworkStatus.LIMITED.value == "limited"
        assert NetworkStatus.UNKNOWN.value == "unknown"

    def test_enum_membership(self):
        """Test all expected statuses exist."""
        from jarvis_core.network.detector import NetworkStatus

        statuses = [s.value for s in NetworkStatus]
        assert "online" in statuses
        assert "offline" in statuses
        assert "limited" in statuses
        assert "unknown" in statuses


class TestEndpointStatus:
    """Tests for EndpointStatus dataclass."""

    def test_creation_success(self):
        """Test EndpointStatus for successful connection."""
        from jarvis_core.network.detector import EndpointStatus

        status = EndpointStatus(
            url="https://api.example.com",
            reachable=True,
            latency_ms=45.5,
            last_checked=datetime.now(),
        )

        assert status.url == "https://api.example.com"
        assert status.reachable is True
        assert status.latency_ms == 45.5
        assert status.error is None

    def test_creation_failure(self):
        """Test EndpointStatus for failed connection."""
        from jarvis_core.network.detector import EndpointStatus

        status = EndpointStatus(
            url="https://api.example.com",
            reachable=False,
            error="Connection timeout",
            last_checked=datetime.now(),
        )

        assert status.reachable is False
        assert status.error == "Connection timeout"
        assert status.latency_ms is None

    def test_creation_minimal(self):
        """Test EndpointStatus with minimal fields."""
        from jarvis_core.network.detector import EndpointStatus

        status = EndpointStatus(url="https://test.com", reachable=True)

        assert status.url == "https://test.com"
        assert status.reachable is True


class TestNetworkCheckResult:
    """Tests for NetworkCheckResult dataclass."""

    def test_is_online_true(self):
        """Test is_online property for ONLINE status."""
        from jarvis_core.network.detector import NetworkCheckResult, NetworkStatus

        result = NetworkCheckResult(status=NetworkStatus.ONLINE, endpoints={})

        assert result.is_online is True
        assert result.is_offline is False

    def test_is_online_limited(self):
        """Test is_online for LIMITED status.

        Note: is_online returns True for LIMITED because the detector's
        is_online method checks for ONLINE or LIMITED status.
        But the NetworkCheckResult.is_online property only returns True for ONLINE.
        """
        from jarvis_core.network.detector import NetworkCheckResult, NetworkStatus

        result = NetworkCheckResult(status=NetworkStatus.LIMITED, endpoints={})

        # NetworkCheckResult.is_online only returns True for ONLINE status
        # This is different from NetworkDetector.is_online which includes LIMITED
        assert result.is_online is False
        assert result.is_offline is False

    def test_is_offline_true(self):
        """Test is_offline for OFFLINE status."""
        from jarvis_core.network.detector import NetworkCheckResult, NetworkStatus

        result = NetworkCheckResult(status=NetworkStatus.OFFLINE, endpoints={})

        assert result.is_online is False
        assert result.is_offline is True

    def test_checked_at_default(self):
        """Test checked_at has default value."""
        from jarvis_core.network.detector import NetworkCheckResult, NetworkStatus

        result = NetworkCheckResult(status=NetworkStatus.ONLINE, endpoints={})

        assert result.checked_at is not None


class TestNetworkDetector:
    """Tests for NetworkDetector class."""

    def test_initialization_default(self):
        """Test default initialization."""
        from jarvis_core.network.detector import NetworkDetector

        detector = NetworkDetector()

        assert detector._timeout == 5.0
        assert detector._cache_ttl == 30.0
        assert len(detector._endpoints) > 0

    def test_initialization_custom_endpoints(self):
        """Test with custom endpoints."""
        from jarvis_core.network.detector import NetworkDetector

        endpoints = ["https://custom1.com", "https://custom2.com"]
        detector = NetworkDetector(check_endpoints=endpoints)

        assert detector._endpoints == endpoints

    def test_initialization_custom_timeout(self):
        """Test with custom timeout."""
        from jarvis_core.network.detector import NetworkDetector

        detector = NetworkDetector(timeout_seconds=10.0)

        assert detector._timeout == 10.0

    def test_initialization_custom_cache_ttl(self):
        """Test with custom cache TTL."""
        from jarvis_core.network.detector import NetworkDetector

        detector = NetworkDetector(cache_ttl_seconds=60.0)

        assert detector._cache_ttl == 60.0

    @patch("jarvis_core.network.detector.socket.socket")
    def test_check_endpoint_success(self, mock_socket_class):
        """Test successful endpoint check."""
        from jarvis_core.network.detector import NetworkDetector

        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.connect.return_value = None

        detector = NetworkDetector(timeout_seconds=1.0)
        result = detector.check_endpoint("https://api.example.com")

        assert result.reachable is True
        assert result.error is None

    @patch("jarvis_core.network.detector.socket.socket")
    def test_check_endpoint_timeout(self, mock_socket_class):
        """Test endpoint check with timeout."""
        from jarvis_core.network.detector import NetworkDetector

        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.connect.side_effect = TimeoutError("Connection timed out")

        detector = NetworkDetector()
        result = detector.check_endpoint("https://slow.example.com")

        assert result.reachable is False
        assert result.error is not None

    @patch("jarvis_core.network.detector.socket.socket")
    def test_check_endpoint_dns_failure(self, mock_socket_class):
        """Test endpoint check with DNS failure."""
        from jarvis_core.network.detector import NetworkDetector

        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.connect.side_effect = socket.gaierror(8, "Name resolution failed")

        detector = NetworkDetector()
        result = detector.check_endpoint("https://nonexistent.invalid")

        assert result.reachable is False
        assert result.error is not None

    @patch("jarvis_core.network.detector.socket.socket")
    def test_check_endpoint_os_error(self, mock_socket_class):
        """Test endpoint check with OS error."""
        from jarvis_core.network.detector import NetworkDetector

        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.connect.side_effect = OSError("Network unreachable")

        detector = NetworkDetector()
        result = detector.check_endpoint("https://example.com")

        assert result.reachable is False
        assert result.error is not None

    def test_should_use_cache_no_cache(self):
        """Test cache check when no cache exists."""
        from jarvis_core.network.detector import NetworkDetector

        detector = NetworkDetector()

        assert detector._should_use_cache() is False

    def test_should_use_cache_valid(self):
        """Test cache check with valid cache."""
        from jarvis_core.network.detector import (
            NetworkDetector,
            NetworkCheckResult,
            NetworkStatus,
        )

        detector = NetworkDetector(cache_ttl_seconds=60.0)
        detector._cached_status = NetworkCheckResult(status=NetworkStatus.ONLINE, endpoints={})
        detector._last_check = time.time()

        assert detector._should_use_cache() is True

    def test_should_use_cache_expired(self):
        """Test cache check with expired cache."""
        from jarvis_core.network.detector import (
            NetworkDetector,
            NetworkCheckResult,
            NetworkStatus,
        )

        detector = NetworkDetector(cache_ttl_seconds=1.0)
        detector._cached_status = NetworkCheckResult(status=NetworkStatus.ONLINE, endpoints={})
        detector._last_check = time.time() - 10  # 10 seconds ago

        assert detector._should_use_cache() is False

    def test_get_status_uses_cache(self):
        """Test get_status uses cache when valid."""
        from jarvis_core.network.detector import (
            NetworkDetector,
            NetworkCheckResult,
            NetworkStatus,
        )

        detector = NetworkDetector(cache_ttl_seconds=60.0)
        detector._cached_status = NetworkCheckResult(status=NetworkStatus.ONLINE, endpoints={})
        detector._last_check = time.time()

        with patch.object(detector, "_check_all_endpoints") as mock_check:
            result = detector.get_status(force_check=False)

            mock_check.assert_not_called()
            assert result.status == NetworkStatus.ONLINE

    def test_get_status_force_check(self):
        """Test get_status with force_check bypasses cache."""
        from jarvis_core.network.detector import (
            NetworkDetector,
            NetworkCheckResult,
            NetworkStatus,
        )

        detector = NetworkDetector()
        detector._cached_status = NetworkCheckResult(status=NetworkStatus.ONLINE, endpoints={})
        detector._last_check = time.time()

        with patch.object(detector, "_check_all_endpoints") as mock_check:
            mock_check.return_value = NetworkCheckResult(status=NetworkStatus.OFFLINE, endpoints={})

            result = detector.get_status(force_check=True)

            mock_check.assert_called_once()
            assert result.status == NetworkStatus.OFFLINE

    def test_is_offline_method(self):
        """Test is_offline method."""
        from jarvis_core.network.detector import NetworkDetector

        detector = NetworkDetector()

        with patch.object(detector, "is_online", return_value=False):
            assert detector.is_offline() is True

        with patch.object(detector, "is_online", return_value=True):
            assert detector.is_offline() is False


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_is_online_function(self):
        """Test is_online convenience function."""
        from jarvis_core.network.detector import is_online

        with patch("jarvis_core.network.detector.get_detector") as mock_get:
            mock_detector = Mock()
            mock_detector.is_online.return_value = True
            mock_get.return_value = mock_detector

            result = is_online()

            assert result is True
            mock_detector.is_online.assert_called_once()

    def test_get_network_status_function(self):
        """Test get_network_status convenience function."""
        from jarvis_core.network.detector import (
            get_network_status,
            NetworkCheckResult,
            NetworkStatus,
        )

        with patch("jarvis_core.network.detector.get_detector") as mock_get:
            mock_detector = Mock()
            mock_detector.get_status.return_value = NetworkCheckResult(
                status=NetworkStatus.ONLINE, endpoints={}
            )
            mock_get.return_value = mock_detector

            result = get_network_status()

            assert result.status == NetworkStatus.ONLINE

    def test_get_detector_singleton(self):
        """Test get_detector returns singleton."""
        from jarvis_core.network import detector as detector_module

        # Reset global
        detector_module._global_detector = None

        d1 = detector_module.get_detector()
        d2 = detector_module.get_detector()

        assert d1 is d2


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.network import (
            NetworkDetector,
            NetworkStatus,
            is_online,
            get_network_status,
        )

        assert NetworkDetector is not None
        assert NetworkStatus is not None
        assert is_online is not None
        assert get_network_status is not None

    def test_all_exports(self):
        """Test __all__ exports."""
        from jarvis_core.network import (
            DegradationLevel,
            DegradationManager,
            OfflineError,
        )

        assert DegradationLevel is not None
        assert DegradationManager is not None
        assert OfflineError is not None
