"""Remediation compatibility shim."""

from __future__ import annotations

from jarvis_core.runtime import remediation as _remediation

__all__ = [name for name in dir(_remediation) if not name.startswith("_")]

globals().update({name: getattr(_remediation, name) for name in __all__})
