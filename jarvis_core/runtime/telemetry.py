"""Runtime telemetry shim."""

from __future__ import annotations


def emit(event: str) -> dict[str, str]:
    """Return a basic telemetry payload."""
    return {"event": event}
