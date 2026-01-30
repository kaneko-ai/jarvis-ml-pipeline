"""Schema helpers for the knowledge base."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class EvidenceRef:
    chunk_id: str
    locator: str
    quote: str
    score: float = 0.0


@dataclass
class ClaimEntry:
    claim_id: str
    text: str
    evidence: list[EvidenceRef] = field(default_factory=list)
    evidence_strength: str = "low"
    tier: str = "C"
    conflict: bool = False
    needs_followup: bool = False
    note: str | None = None


@dataclass
class PaperMeta:
    pmid: str
    title: str
    doi: str = ""
    year: int | None = None
    journal: str = ""
    oa: str = "unknown"
    tier: str = "C"
    score: float = 0.0
    run_id: str = ""
    tags: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TopicMeta:
    topic: str
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class RunSummary:
    run_id: str
    papers: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def format_front_matter(data: dict[str, Any]) -> str:
    """Create a minimal YAML front matter string."""

    def render_value(value: Any) -> str:
        if isinstance(value, list):
            rendered = [render_value(item) for item in value]
            return f"[{', '.join(rendered)}]"
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value)
        escaped = text.replace('"', '\\"')
        return f'"{escaped}"'

    lines = ["---"]
    for key, value in data.items():
        lines.append(f"{key}: {render_value(value)}")
    lines.append("---")
    return "\n".join(lines)


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML-ish front matter and return (data, body)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n")
    end_idx = None
    for idx in range(1, len(parts)):
        if parts[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return {}, text
    fm_lines = parts[1:end_idx]
    body = "\n".join(parts[end_idx + 1 :]).lstrip("\n")
    data: dict[str, Any] = {}
    for line in fm_lines:
        if not line.strip() or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value.startswith("[") and raw_value.endswith("]"):
            inner = raw_value[1:-1].strip()
            if not inner:
                data[key] = []
            else:
                items = [item.strip().strip('"') for item in inner.split(",")]
                data[key] = items
        elif raw_value.lower() in {"true", "false"}:
            data[key] = raw_value.lower() == "true"
        elif raw_value.lower() == "null":
            data[key] = None
        else:
            data[key] = raw_value.strip('"')
    return data, body
