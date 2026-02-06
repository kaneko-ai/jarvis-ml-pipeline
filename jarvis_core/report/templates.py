"""Report template helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReportTemplate:
    """Simple report template."""

    name: str = "default"
    body: str = "{content}"


def get_default_template() -> ReportTemplate:
    """Return the default report template."""
    return ReportTemplate()


__all__ = ["ReportTemplate", "get_default_template"]
