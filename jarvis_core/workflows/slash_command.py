"""Slash command parser for workflows."""

from __future__ import annotations

import re


def parse_slash_command(input_text: str) -> tuple[str | None, str]:
    """Parse slash command input into workflow name and remaining text."""
    match = re.match(r"^/([\\w-]+)\\s*(.*)$", input_text.strip())
    if not match:
        return None, input_text
    name = match.group(1)
    remaining = match.group(2).strip()
    return name, remaining
