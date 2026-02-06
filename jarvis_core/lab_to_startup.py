"""Lab-to-startup helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StartupPlan:
    """Simple startup plan."""

    summary: str = ""


def build_startup_plan(lab_name: str) -> StartupPlan:
    """Build a startup plan from a lab name.

    Args:
        lab_name: Lab name.

    Returns:
        StartupPlan.
    """
    return StartupPlan(summary=f"Plan for {lab_name}")


__all__ = ["StartupPlan", "build_startup_plan"]
