"""Contradiction resolver compatibility shim."""

from __future__ import annotations

from jarvis_core.contradiction.resolution import (
    ContradictionResolver,
    ResolutionStrategy,
    ResolutionSuggestion,
)

__all__ = ["ContradictionResolver", "ResolutionStrategy", "ResolutionSuggestion"]
