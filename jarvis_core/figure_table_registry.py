"""Figure/table registry helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FigureTableEntry:
    """Registry entry for figure or table."""

    identifier: str
    kind: str = "figure"


class FigureTableRegistry:
    """Minimal registry for figures and tables."""

    def __init__(self) -> None:
        self._entries: list[FigureTableEntry] = []

    def register(self, entry: FigureTableEntry) -> None:
        """Register an entry.

        Args:
            entry: Entry to register.
        """
        self._entries.append(entry)

    def list_entries(self) -> list[FigureTableEntry]:
        """Return all entries."""
        return list(self._entries)


__all__ = ["FigureTableEntry", "FigureTableRegistry"]
