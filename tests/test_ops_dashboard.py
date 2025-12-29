from __future__ import annotations

from pathlib import Path

import pytest


def test_ops_dashboard_renders():
    playwright = pytest.importorskip("playwright.sync_api")
    ops_path = Path(__file__).resolve().parents[1] / "dashboard" / "ops.html"
    assert ops_path.exists()

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(ops_path.as_uri())
        page.wait_for_timeout(500)
        content = page.content()
        browser.close()

    assert "Ops Dashboard" in content
