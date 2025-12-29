import os
import time

import pytest
import requests

pytestmark = pytest.mark.core

API_BASE = os.getenv("API_BASE", "http://localhost:8000").rstrip("/")
RUN_ID = os.getenv("RUN_ID", "RUN_SMOKE_001")


def _get(url: str):
    return requests.get(url, timeout=10)


def _allow_status(response, allowed):
    assert response.status_code in allowed, (
        f"Unexpected status {response.status_code} for {response.url}"
    )


@pytest.mark.parametrize(
    "path,allowed",
    [
        ("/api/health", {200}),
        ("/api/capabilities", {200}),
        ("/api/runs", {200, 501}),
    ],
)
def test_smoke_endpoints(path, allowed):
    res = _get(f"{API_BASE}{path}")
    _allow_status(res, allowed)


def test_smoke_run_detail_and_files():
    run_id = RUN_ID
    runs_res = _get(f"{API_BASE}/api/runs")
    if runs_res.status_code == 200:
        payload = runs_res.json()
        runs = payload.get("runs", payload) if isinstance(payload, dict) else payload
        if runs:
            run_id = runs[0].get("run_id", run_id)
    else:
        _allow_status(runs_res, {501})

    detail_res = _get(f"{API_BASE}/api/runs/{run_id}")
    _allow_status(detail_res, {200, 404, 501})

    files_res = _get(f"{API_BASE}/api/runs/{run_id}/files")
    _allow_status(files_res, {200, 404, 501})


def test_smoke_unimplemented_returns_501():
    res = _get(f"{API_BASE}/api/submission/decision")
    if res.status_code != 501:
        pytest.skip("submission/decision is implemented")

    time.sleep(0.1)
