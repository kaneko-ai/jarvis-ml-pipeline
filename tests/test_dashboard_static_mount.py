from __future__ import annotations

import pytest

from jarvis_web.app import FASTAPI_AVAILABLE, app

pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI is not available")


def test_dashboard_route_redirects_to_trailing_slash() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code in {307, 308}
    assert response.headers.get("location") == "/dashboard/"


def test_dashboard_static_index_is_served() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/dashboard/index.html")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
