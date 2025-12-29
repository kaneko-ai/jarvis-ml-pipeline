"""Citation formatting helpers."""
from __future__ import annotations

from typing import Iterable, Mapping


def format_evidence_items(evidence: Iterable[Mapping]) -> str:
    lines = []
    for item in evidence:
        locator = item.get("locator") or item.get("section") or ""
        chunk_id = item.get("chunk_id") or item.get("chunkId") or ""
        quote = item.get("quote") or item.get("snippet") or ""
        quote = quote.replace("\n", " ").strip()
        if quote:
            quote = f'"{quote}"'
        parts = []
        if locator:
            parts.append(f"Section: {locator}")
        if chunk_id:
            parts.append(f"chunk_id={chunk_id}")
        if quote:
            parts.append(f"文章抜粋: {quote}")
        if parts:
            lines.append(" / ".join(parts))
    return "; ".join(lines) if lines else "根拠情報なし"
