import os
from unittest.mock import patch


def test_finance_route_flag_off():
    """Test that finance router is NOT included when flag is OFF."""
    with patch.dict(os.environ, {"JARVIS_ENABLE_FINANCE": "0"}):
        # We need to reload or import app inside the test to check the effect
        import importlib
        import jarvis_web.app

        importlib.reload(jarvis_web.app)

        app = jarvis_web.app.app
        if app is None:
            return  # FastAPI not available

        routes = [route.path for route in app.routes]
        assert "/api/finance/simulate" not in routes


def test_finance_route_flag_on():
    """Test that finance router IS included when flag is ON."""
    with patch.dict(os.environ, {"JARVIS_ENABLE_FINANCE": "1"}):
        import importlib
        import jarvis_web.app

        importlib.reload(jarvis_web.app)

        app = jarvis_web.app.app
        if app is None:
            return  # FastAPI not available

        routes = [route.path for route in app.routes]
        assert "/api/finance/simulate" in routes