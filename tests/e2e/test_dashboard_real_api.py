from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time

import pytest
import requests
from playwright.sync_api import Page, expect


@pytest.fixture(scope="module")
def api_server() -> str:
    """Start a real API server for dashboard integration checks."""
    if importlib.util.find_spec("uvicorn") is None:
        pytest.skip("uvicorn is not installed; install the 'web' extra to run this e2e test")

    env = os.environ.copy()
    env["AUTH_MODE"] = "disabled"
    env["JARVIS_ENV"] = "development"
    env["PYTHONPATH"] = "."
    port = "8089"

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "jarvis_web.app:app",
            "--port",
            port,
            "--log-level",
            "info",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
    )

    url = f"http://localhost:{port}"
    success = False
    last_error = ""
    for i in range(30):
        try:
            resp = requests.get(f"{url}/api/health", timeout=2)
            if resp.status_code == 200:
                success = True
                break
        except Exception as exc:  # pragma: no cover - network/environment dependent
            last_error = str(exc)
        time.sleep(1)

    if not success:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
        else:
            process.terminate()
        raise RuntimeError(f"API server failed to start on {url}. Last error: {last_error}")

    yield url

    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
    else:
        process.terminate()


@pytest.fixture(scope="module")
def dashboard_server() -> str:
    """Serve dashboard static files for browser automation."""
    port = "8081"
    process = subprocess.Popen(
        [sys.executable, "-m", "http.server", port, "--directory", "dashboard"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    url = f"http://localhost:{port}"
    success = False
    for _ in range(10):
        try:
            resp = requests.get(url, timeout=1)
            if resp.status_code == 200:
                success = True
                break
        except Exception:  # pragma: no cover - network/environment dependent
            pass
        time.sleep(1)

    if not success:
        process.terminate()
        raise RuntimeError(f"Dashboard server failed to start on {url}")

    yield url
    process.terminate()


def test_dashboard_real_api_integration(api_server: str, dashboard_server: str, page: Page) -> None:
    """Verify dashboard behavior against a real local API server."""
    page.goto(f"{dashboard_server}/settings.html")
    page.fill('[data-testid="api-base"]', api_server)
    page.fill('[data-testid="api-token"]', "test-token")
    page.click('[data-testid="save-settings"]')

    page.goto(f"{dashboard_server}/ops.html")
    api_status_card = page.locator('.status-card[data-key="api"]')
    api_badge = api_status_card.locator('[data-role="status"]')
    expect(api_badge).to_contain_text("ok", timeout=15000, ignore_case=True)

    page.goto(f"{dashboard_server}/index.html")
    latest_runs = page.locator("#latest-runs")
    expect(latest_runs).to_be_visible()

    empty_notice = page.locator("#latest-runs-empty").first
    has_rows = page.evaluate(
        """
        () => {
          const container = document.querySelector("#latest-runs");
          if (!container) return false;
          const rows = container.querySelectorAll("tr, li, .run-item, .row");
          return rows.length > 0;
        }
        """
    )
    if has_rows:
        expect(empty_notice).to_be_hidden()
    else:
        expect(empty_notice).to_be_visible()
