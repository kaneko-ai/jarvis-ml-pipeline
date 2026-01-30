"""Schema for claim provenance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceItem:
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


@dataclass
class ClaimUnit:
    claim_id: str
    paper_id: str
    claim_text: str
    claim_type: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    generated_at: str = ""
    model_info: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "paper_id": self.paper_id,
            "claim_text": self.claim_text,
            "claim_type": self.claim_type,
            "evidence": [item.to_dict() for item in self.evidence],
            "generated_at": self.generated_at,
            "model_info": self.model_info,
        }