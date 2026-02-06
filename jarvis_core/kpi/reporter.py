"""KPI reporting helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KPIReport:
    """Lightweight KPI report container."""

    metrics: dict[str, Any] = field(default_factory=dict)


class KPIReporter:
    """Minimal KPI reporter."""

    def report(self) -> KPIReport:
        """Return an empty KPI report."""
        return KPIReport()
