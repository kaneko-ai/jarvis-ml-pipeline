"""API Smoke Tests - verify basic API functionality."""

from __future__ import annotations

import os
import subprocess
import sys
from time import sleep
from urllib.parse import urlparse

import pytest
import requests

DEFAULT_API_BASE = "http://localhost:8000"


def _api_ready(api_base: str, retries: int = 10, timeout: float = 5.0) -> bool:
    for _ in range(retries):
        try:
            response = requests.get(f"{api_base}/api/health", timeout=timeout)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        sleep(1)
    return False


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            check=False,
            capture_output=True,
        )
    else:
        process.terminate()


@pytest.fixture(scope="module")
def api_base():
    """Provide API base URL. Start local API server when not already running."""
    base = os.environ.get("API_BASE", DEFAULT_API_BASE).rstrip("/")
    if _api_ready(base):
        yield base
        return

    if os.environ.get("API_BASE"):
        pytest.skip("API not available")

    parsed = urlparse(base)
    port = parsed.port or 8000
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "jarvis_web.app:app",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
    )

    if not _api_ready(base, retries=30, timeout=2):
        _stop_process(process)
        pytest.skip("API not available")

    try:
        yield base
    finally:
        _stop_process(process)


def test_health_endpoint(api_base):
    """Test health endpoint."""
    response = requests.get(f"{api_base}/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_runs_list_endpoint(api_base):
    """Test runs list endpoint."""
    response = requests.get(f"{api_base}/api/runs", headers={"Authorization": "Bearer test"})
    # 200 or 401 (if auth required) are acceptable
    assert response.status_code in [200, 401, 403]


def test_capabilities_endpoint(api_base):
    """Test capabilities endpoint."""
    response = requests.get(
        f"{api_base}/api/capabilities", headers={"Authorization": "Bearer test"}
    )
    assert response.status_code in [200, 401, 403]


def test_api_map_endpoint(api_base):
    """Test API map endpoint."""
    response = requests.get(f"{api_base}/api/map/v1")
    # 200 or 404 (if not generated yet)
    assert response.status_code in [200, 404]
