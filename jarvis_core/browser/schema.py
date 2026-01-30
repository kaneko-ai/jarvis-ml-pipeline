"""Schemas for browser subagent operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BrowserAction(Enum):
    """Supported browser actions."""

    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_DOM = "extract_dom"
    WAIT = "wait"
    EXECUTE_JS = "execute_js"


@dataclass
class BrowserState:
    """Snapshot of current browser state."""

    current_url: str | None = None
    title: str | None = None
    dom_snapshot: str | None = None
    screenshot_base64: str | None = None
    console_logs: list[str] = field(default_factory=list)


@dataclass
class BrowserActionResult:
    """Result for a browser action."""

    action: BrowserAction
    success: bool
    data: Any = None
    error: str | None = None
    screenshot: str | None = None
    duration_ms: float | None = None


@dataclass
class SecurityPolicy:
    """Security policy for browser automation."""

    js_execution: bool = False
    url_allow_list: list[str] = field(default_factory=list)
    url_deny_list: list[str] = field(default_factory=list)