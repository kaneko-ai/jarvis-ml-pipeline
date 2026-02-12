from __future__ import annotations

from pathlib import Path

import pytest
from playwright.async_api import async_playwright

from async_test_utils import sync_async_test


@sync_async_test
async def test_ops_dashboard_renders():
    pytest.importorskip("playwright.async_api")
    ops_path = Path(__file__).resolve().parents[1] / "dashboard" / "ops.html"
    assert ops_path.exists()

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
        except Exception as exc:  # pragma: no cover - environment dependent
            pytest.skip(f"Playwright browser is unavailable in this environment: {exc}")
        page = await browser.new_page()
        await page.goto(ops_path.as_uri())
        await page.wait_for_timeout(500)
        content = await page.content()
        await browser.close()

    assert "Ops Dashboard" in content
