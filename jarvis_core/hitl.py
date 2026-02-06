"""HITL compatibility shim."""

from __future__ import annotations

from jarvis_core.ops import hitl as _hitl

__all__ = [name for name in dir(_hitl) if not name.startswith("_")]

globals().update({name: getattr(_hitl, name) for name in __all__})
