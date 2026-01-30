"""Network Status Detector.

Provides network connectivity detection for offline mode support.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.5.1
"""

from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class NetworkStatus(Enum):
    """Network connectivity status."""

    ONLINE = "online"
    OFFLINE = "offline"
    LIMITED = "limited"  # Some endpoints reachable but not all
    UNKNOWN = "unknown"


@dataclass
class EndpointStatus:
    """Status of a specific endpoint."""

    url: str
    reachable: bool
    latency_ms: float | None = None
    last_checked: datetime | None = None
    error: str | None = None


@dataclass
class NetworkCheckResult:
    """Result of a network status check."""

    status: NetworkStatus
    endpoints: dict[str, EndpointStatus] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.now)

    @property
    def is_online(self) -> bool:
        """Check if network is online."""
        return self.status == NetworkStatus.ONLINE

    @property
    def is_offline(self) -> bool:
        """Check if network is offline."""
        return self.status == NetworkStatus.OFFLINE


# Default endpoints to check for connectivity
DEFAULT_CHECK_ENDPOINTS = [
    "https://api.semanticscholar.org",
    "https://eutils.ncbi.nlm.nih.gov",
    "https://api.openalex.org",
    "https://api.crossref.org",
]


class NetworkDetector:
    """Detects network connectivity status.

    Supports checking multiple endpoints and determining overall network status.
    Uses caching to avoid excessive network checks.

    Example:
        >>> detector = NetworkDetector()
        >>> if detector.is_online():
        ...     print("Network available")
        ... else:
        ...     print("Working offline")
    """

    def __init__(
        self,
        check_endpoints: list[str] | None = None,
        timeout_seconds: float = 5.0,
        cache_ttl_seconds: float = 30.0,
    ):
        """Initialize the network detector.

        Args:
            check_endpoints: List of URLs to check for connectivity
            timeout_seconds: Timeout for each endpoint check
            cache_ttl_seconds: How long to cache network status
        """
        self._endpoints = check_endpoints or DEFAULT_CHECK_ENDPOINTS
        self._timeout = timeout_seconds
        self._cache_ttl = cache_ttl_seconds

        self._cached_status: NetworkCheckResult | None = None
        self._last_check: float | None = None

    def is_online(self, force_check: bool = False) -> bool:
        """Check if network is available.

        Args:
            force_check: If True, bypass cache and check now

        Returns:
            True if at least one endpoint is reachable
        """
        status = self.get_status(force_check=force_check)
        return status.status in (NetworkStatus.ONLINE, NetworkStatus.LIMITED)

    def is_offline(self, force_check: bool = False) -> bool:
        """Check if network is unavailable.

        Args:
            force_check: If True, bypass cache and check now

        Returns:
            True if all endpoints are unreachable
        """
        return not self.is_online(force_check=force_check)

    def get_status(self, force_check: bool = False) -> NetworkCheckResult:
        """Get detailed network status.

        Args:
            force_check: If True, bypass cache and check now

        Returns:
            NetworkCheckResult with detailed status information
        """
        # Check cache
        if not force_check and self._should_use_cache():
            return self._cached_status  # type: ignore

        # Perform check
        result = self._check_all_endpoints()

        # Update cache
        self._cached_status = result
        self._last_check = time.time()

        return result

    def check_endpoint(self, url: str) -> EndpointStatus:
        """Check if a specific endpoint is reachable.

        Args:
            url: URL to check

        Returns:
            EndpointStatus with reachability information
        """
        start_time = time.time()

        try:
            parsed = urlparse(url)
            host = parsed.netloc or parsed.path
            port = parsed.port or (443 if parsed.scheme == "https" else 80)

            # Try TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self._timeout)

            try:
                sock.connect((host, port))
                latency_ms = (time.time() - start_time) * 1000

                return EndpointStatus(
                    url=url,
                    reachable=True,
                    latency_ms=latency_ms,
                    last_checked=datetime.now(),
                )
            finally:
                sock.close()

        except TimeoutError:
            return EndpointStatus(
                url=url,
                reachable=False,
                last_checked=datetime.now(),
                error="Connection timeout",
            )
        except socket.gaierror as e:
            return EndpointStatus(
                url=url,
                reachable=False,
                last_checked=datetime.now(),
                error=f"DNS resolution failed: {e}",
            )
        except OSError as e:
            return EndpointStatus(
                url=url,
                reachable=False,
                last_checked=datetime.now(),
                error=str(e),
            )

    def _should_use_cache(self) -> bool:
        """Check if cached status should be used."""
        if self._cached_status is None or self._last_check is None:
            return False

        elapsed = time.time() - self._last_check
        return elapsed < self._cache_ttl

    def _check_all_endpoints(self) -> NetworkCheckResult:
        """Check all configured endpoints."""
        endpoints: dict[str, EndpointStatus] = {}
        reachable_count = 0

        for url in self._endpoints:
            status = self.check_endpoint(url)
            endpoints[url] = status
            if status.reachable:
                reachable_count += 1
                logger.debug(f"Endpoint reachable: {url} ({status.latency_ms:.0f}ms)")
            else:
                logger.debug(f"Endpoint unreachable: {url} ({status.error})")

        # Determine overall status
        if reachable_count == len(self._endpoints):
            status = NetworkStatus.ONLINE
        elif reachable_count > 0:
            status = NetworkStatus.LIMITED
        else:
            status = NetworkStatus.OFFLINE

        logger.info(
            f"Network status: {status.value} ({reachable_count}/{len(self._endpoints)} endpoints)"
        )

        return NetworkCheckResult(
            status=status,
            endpoints=endpoints,
            checked_at=datetime.now(),
        )


# Global detector instance
_global_detector: NetworkDetector | None = None


def get_detector() -> NetworkDetector:
    """Get the global network detector instance."""
    global _global_detector
    if _global_detector is None:
        _global_detector = NetworkDetector()
    return _global_detector


def is_online(force_check: bool = False) -> bool:
    """Check if network is available (convenience function).

    Args:
        force_check: If True, bypass cache and check now

    Returns:
        True if network is available
    """
    return get_detector().is_online(force_check=force_check)


def get_network_status(force_check: bool = False) -> NetworkCheckResult:
    """Get detailed network status (convenience function).

    Args:
        force_check: If True, bypass cache and check now

    Returns:
        NetworkCheckResult with detailed status
    """
    return get_detector().get_status(force_check=force_check)
