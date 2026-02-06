"""Calendar builder helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CalendarEntry:
    """Calendar entry."""

    title: str
    day: str


class CalendarBuilder:
    """Minimal calendar builder."""

    def build(self, entries: list[CalendarEntry]) -> list[CalendarEntry]:
        """Build a calendar.

        Args:
            entries: Calendar entries.

        Returns:
            List of entries (pass-through).
        """
        return list(entries)


__all__ = ["CalendarBuilder", "CalendarEntry"]
