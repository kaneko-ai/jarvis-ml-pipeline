"""Debug helpers for devtools."""

from __future__ import annotations


class DebugTool:
    """Minimal debug tool."""

    def dump(self) -> dict:
        """Return a placeholder debug payload."""
        return {"debug": True}
