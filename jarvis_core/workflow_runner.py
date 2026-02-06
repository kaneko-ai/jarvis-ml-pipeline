"""Workflow runner compatibility shim."""

from __future__ import annotations

from jarvis_core.workflow import runner as _runner

__all__ = [name for name in dir(_runner) if not name.startswith("_")]

globals().update({name: getattr(_runner, name) for name in __all__})
