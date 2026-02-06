"""Lambda modules compatibility shim."""

from __future__ import annotations

from jarvis_core.experimental import lambda_modules as _lambda_modules

__all__ = [name for name in dir(_lambda_modules) if not name.startswith("_")]

globals().update({name: getattr(_lambda_modules, name) for name in __all__})
