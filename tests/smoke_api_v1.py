"""API Smoke Tests - verify basic API functionality."""

import os
import pytest
import requests
from time import sleep

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")


@pytest.fixture(scope="module")
def wait_for_api():
    """Wait for API to be ready."""
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_BASE}/api/health", timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        sleep(1)
    pytest.skip("API not available")


def test_health_endpoint(wait_for_api):
    """Test health endpoint."""
    response = requests.get(f"{API_BASE}/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_runs_list_endpoint(wait_for_api):
    """Test runs list endpoint."""
    response = requests.get(f"{API_BASE}/api/runs", headers={"Authorization": "Bearer test"})
    # 200 or 401 (if auth required) are acceptable
    assert response.status_code in [200, 401, 403]


def test_capabilities_endpoint(wait_for_api):
    """Test capabilities endpoint."""
    response = requests.get(
        f"{API_BASE}/api/capabilities", headers={"Authorization": "Bearer test"}
    )
    assert response.status_code in [200, 401, 403]


def test_api_map_endpoint(wait_for_api):
    """Test API map endpoint."""
    response = requests.get(f"{API_BASE}/api/map/v1")
    # 200 or 404 (if not generated yet)
    assert response.status_code in [200, 404]
