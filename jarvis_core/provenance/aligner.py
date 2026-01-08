"""Align claims to evidence chunks."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any


@dataclass
class EvidenceCandidate:
    chunk_id: str
    locator: dict[str, Any]
    quote: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "locator": self.locator,
            "quote": self.quote,
            "score": self.score,
        }


def align_claim_to_chunks(claim_text: str, chunks: Iterable[dict[str, Any]], top_k: int = 3) -> list[EvidenceCandidate]:
    candidates: list[EvidenceCandidate] = []
    for chunk in chunks:
        text = (chunk.get("text") or "").strip()
        if not text:
            continue
        score = _similarity(claim_text, text)
        locator = {
            "section": chunk.get("section") or "",
            "paragraph_index": chunk.get("paragraph_index") or 0,
            "sentence_index": 0,
        }
        quote = " ".join(text.split()[:25])
        candidates.append(
            EvidenceCandidate(
                chunk_id=chunk.get("chunk_id") or "",
                locator=locator,
                quote=quote,
                score=score,
            )
        )
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:top_k] if candidates else []


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()
