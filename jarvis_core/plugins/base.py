"""Plugin base abstractions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PluginInfo:
    """Basic plugin metadata."""

    name: str = "plugin"
    version: str = "0.1.0"


class PluginBase:
    """Minimal plugin base class."""

    def info(self) -> PluginInfo:
        """Return plugin metadata."""
        return PluginInfo()
