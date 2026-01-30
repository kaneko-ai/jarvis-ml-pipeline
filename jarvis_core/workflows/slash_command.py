"""Slash command parser for workflows."""

from __future__ import annotations


def parse_slash_command(input_text: str) -> tuple[str | None, str]:
    stripped = input_text.strip()
    if not stripped.startswith("/"):
        return None, input_text
    parts = stripped.split(maxsplit=1)
    command = parts[0][1:]
    if not command:
        return None, input_text
    remaining = parts[1] if len(parts) > 1 else ""
    return command, remaining