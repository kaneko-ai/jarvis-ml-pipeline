"""Merge updates into existing notes while preserving manual edits."""
from __future__ import annotations


def _replace_between(text: str, start: str, end: str, replacement: str) -> str:
    if start in text and end in text:
        before, rest = text.split(start, 1)
        _, after = rest.split(end, 1)
        return f"{before}{start}\n{replacement}\n{end}{after}"
    return ""


def merge_sections(existing: str, sections: dict[str, tuple[str, str, str]]) -> str:
    """Merge multiple sections.

    sections: name -> (start_marker, end_marker, new_content)
    """
    updated = existing
    for _, (start, end, content) in sections.items():
        replaced = _replace_between(updated, start, end, content)
        if replaced:
            updated = replaced
        else:
            updated = f"{updated.rstrip()}\n\n{start}\n{content}\n{end}\n"
    return updated
