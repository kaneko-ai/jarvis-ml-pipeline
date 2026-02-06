"""Public gap analysis shim."""

from __future__ import annotations

from .experimental.gap_analysis import score_research_gaps  # noqa: F401

__all__ = ["score_research_gaps"]
