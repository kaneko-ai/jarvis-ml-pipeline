"""Evidence locator formatting utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class EvidenceLocator:
    """Normalized evidence locator."""

    paper_id: str
    chunk_id: str
    section: str
    paragraph: str
    sentence: str
    weak: bool = False


def _safe(value: Optional[object], fallback: str = "unknown") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def format_evidence_locator(evidence_items: Iterable[EvidenceLocator]) -> str:
    """Format evidence locator string for paragraph suffix."""
    items = list(evidence_items)
    if not items:
        return "【根拠: unknown】"

    parts: List[str] = []
    for item in items[:3]:
        parts.append(
            f"{_safe(item.paper_id)}, {_safe(item.chunk_id)}, {_safe(item.section)} ¶ {_safe(item.paragraph)} {_safe(item.sentence)}"
        )
    return f"【根拠: {'; '.join(parts)}】"


def has_weak_evidence(evidence_items: Iterable[EvidenceLocator]) -> bool:
    return any(item.weak for item in evidence_items)
