"""Context packaging helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ContextPackage:
    """Packaged context."""

    data: dict[str, Any]


class ContextPackager:
    """Minimal context packager."""

    def package(self, data: dict[str, Any]) -> ContextPackage:
        """Package context data.

        Args:
            data: Context data.

        Returns:
            ContextPackage.
        """
        return ContextPackage(data=dict(data))


__all__ = ["ContextPackage", "ContextPackager"]
