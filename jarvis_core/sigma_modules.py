"""Sigma modules compatibility shim."""

from __future__ import annotations

from jarvis_core.experimental import sigma_modules as _sigma_modules

__all__ = [name for name in dir(_sigma_modules) if not name.startswith("_")]

globals().update({name: getattr(_sigma_modules, name) for name in __all__})
