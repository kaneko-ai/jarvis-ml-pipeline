from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from jarvis_web.app import create_app


def test_capabilities_route_is_unique() -> None:
    app = create_app()
    matches = [route for route in app.router.routes if getattr(route, "path", None) == "/api/capabilities"]
    assert len(matches) == 1
