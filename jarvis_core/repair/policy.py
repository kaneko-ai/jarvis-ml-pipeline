"""Repair policy helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RepairDecision:
    """Decision for repair action."""

    action: str = "none"


class RepairPolicy:
    """Simple repair policy."""

    def decide(self, issue: str) -> RepairDecision:
        """Decide a repair action.

        Args:
            issue: Issue description.

        Returns:
            RepairDecision.
        """
        _ = issue
        return RepairDecision(action="none")


__all__ = ["RepairDecision", "RepairPolicy"]
