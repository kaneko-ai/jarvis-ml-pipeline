"""Network Guard for Tests.

Per PR-65, blocks network access during tests unless explicitly allowed.
"""
import pytest
import socket


# Store original socket functions
_original_socket = socket.socket


class NetworkBlockedError(Exception):
    """Raised when network access is attempted during tests."""
    pass


def _blocked_socket(*args, **kwargs):
    """Replacement socket that blocks all connections."""
    raise NetworkBlockedError(
        "Network access is blocked during tests. "
        "Use @pytest.mark.network to allow network access, "
        "or use recorded fixtures."
    )


@pytest.fixture(autouse=True)
def block_network(request):
    """Automatically block network access unless @pytest.mark.network is used."""
    # Check if test has network marker
    if request.node.get_closest_marker("network"):
        # Allow network access
        yield
        return

    # Block network access
    socket.socket = _blocked_socket

    try:
        yield
    finally:
        # Restore original socket
        socket.socket = _original_socket


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )
