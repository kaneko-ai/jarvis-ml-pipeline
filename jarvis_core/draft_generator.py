"""Draft generator compatibility shim."""

from __future__ import annotations

from jarvis_core.writing import draft_generator as _draft_generator

# Re-export public symbols from the writing module.
__all__ = [name for name in dir(_draft_generator) if not name.startswith("_")]

globals().update({name: getattr(_draft_generator, name) for name in __all__})
