"""Observability dashboard helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DashboardSnapshot:
    """Snapshot of dashboard metrics."""

    metrics: dict[str, Any] = field(default_factory=dict)


class ObservabilityDashboard:
    """Minimal dashboard aggregator."""

    def snapshot(self) -> DashboardSnapshot:
        """Return a snapshot of current metrics."""
        return DashboardSnapshot(metrics={})


__all__ = ["DashboardSnapshot", "ObservabilityDashboard"]
