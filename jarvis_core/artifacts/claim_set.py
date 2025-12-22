"""ClaimSet - structured claim-first output.

Per RP-15, forces answer generation to be claim-first with citations.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional
from enum import Enum


class ClaimType(Enum):
    FACT = "fact"
    INFERENCE = "inference"


@dataclass
class Claim:
    """A single claim with citations."""

    claim_id: str
    text: str
    claim_type: ClaimType
    citations: List[str]  # chunk_ids
    confidence: float = 1.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["claim_type"] = self.claim_type.value
        return d


@dataclass
class ClaimSet:
    """Collection of claims with gaps tracking."""

    claims: List[Claim] = field(default_factory=list)
    notes: str = ""
    gaps: List[str] = field(default_factory=list)  # Unsupported areas

    def add_claim(
        self,
        text: str,
        citations: List[str],
        claim_type: ClaimType = ClaimType.FACT,
        confidence: float = 1.0,
    ) -> Claim:
        """Add a claim."""
        claim = Claim(
            claim_id=f"c{len(self.claims) + 1}",
            text=text,
            claim_type=claim_type,
            citations=citations,
            confidence=confidence,
        )
        self.claims.append(claim)
        return claim

    def add_gap(self, description: str) -> None:
        """Record an unsupported area."""
        self.gaps.append(description)

    @property
    def has_unsupported(self) -> bool:
        """Check if any claims lack citations."""
        return any(len(c.citations) == 0 for c in self.claims) or bool(self.gaps)

    @property
    def citation_coverage(self) -> float:
        """Proportion of claims with citations."""
        if not self.claims:
            return 0.0
        return sum(1 for c in self.claims if c.citations) / len(self.claims)

    def to_dict(self) -> dict:
        return {
            "claims": [c.to_dict() for c in self.claims],
            "notes": self.notes,
            "gaps": self.gaps,
            "citation_coverage": round(self.citation_coverage, 4),
        }

    def render_markdown(self) -> str:
        """Render as markdown text."""
        lines = []

        for claim in self.claims:
            cite_str = ", ".join(f"[{c}]" for c in claim.citations) if claim.citations else "[根拠なし]"
            prefix = "■" if claim.claim_type == ClaimType.FACT else "□"
            lines.append(f"{prefix} {claim.text} {cite_str}")

        if self.gaps:
            lines.append("")
            lines.append("### 根拠不足の領域:")
            for gap in self.gaps:
                lines.append(f"- {gap}")

        return "\n".join(lines)

    @classmethod
    def from_dict(cls, data: dict) -> "ClaimSet":
        """Create from dict."""
        claims = []
        for c in data.get("claims", []):
            claims.append(Claim(
                claim_id=c["claim_id"],
                text=c["text"],
                claim_type=ClaimType(c["claim_type"]),
                citations=c["citations"],
                confidence=c.get("confidence", 1.0),
            ))
        return cls(
            claims=claims,
            notes=data.get("notes", ""),
            gaps=data.get("gaps", []),
        )
