"""Web package."""

try:
    from .app import create_app, run_server
    from .dashboard import DashboardAPI

    __all__ = ["create_app", "run_server", "DashboardAPI"]
except ImportError:
    try:
        from .dashboard import DashboardAPI

        __all__ = ["DashboardAPI"]
    except ImportError:
        __all__ = []
