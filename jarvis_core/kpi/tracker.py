"""KPI tracking utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KPIRecord:
    """Single KPI record."""

    name: str
    value: float
    meta: dict[str, Any] = field(default_factory=dict)


class KPITracker:
    """Track KPI records in memory."""

    def __init__(self) -> None:
        """Initialize tracker."""
        self._records: list[KPIRecord] = []

    def record(self, name: str, value: float, meta: dict[str, Any] | None = None) -> None:
        """Record a KPI value.

        Args:
            name: KPI name.
            value: KPI value.
            meta: Optional metadata.
        """
        self._records.append(KPIRecord(name=name, value=value, meta=meta or {}))

    def list_records(self) -> list[KPIRecord]:
        """Return all recorded KPIs."""
        return list(self._records)


__all__ = ["KPIRecord", "KPITracker"]
