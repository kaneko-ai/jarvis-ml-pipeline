"""Triage by Risk.

Per V4-D01, this sorts items by risk score for review prioritization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..artifacts.schema import ArtifactBase


@dataclass
class TriageResult:
    """Result of triage."""

    item_id: str
    item_type: str  # fact, inference, recommendation
    content: str
    risk_score: float
    risk_reasons: list[str]

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "content": self.content[:100],
            "risk_score": round(self.risk_score, 3),
            "risk_reasons": self.risk_reasons,
        }


def calculate_risk_score(
    item: dict,
    item_type: str,
) -> tuple[float, list[str]]:
    """Calculate risk score for an item.

    Args:
        item: Item dict with content and metadata.
        item_type: Type of item.

    Returns:
        Tuple of (risk_score, reasons).
    """
    score = 0.0
    reasons = []

    # FACT without evidence is high risk
    if item_type == "fact":
        if not item.get("has_evidence", False):
            score += 0.5
            reasons.append("FACT without evidence")
        if item.get("confidence", 1.0) < 0.5:
            score += 0.2
            reasons.append("Low confidence")

    # INFERENCE claimed as fact is risky
    if item_type == "inference":
        if "降格" in item.get("content", ""):
            score += 0.3
            reasons.append("Downgraded from FACT")

    # Low alignment score
    if item.get("alignment_score", 1.0) < 0.5:
        score += 0.3
        reasons.append("Low alignment with evidence")

    return min(score, 1.0), reasons


def triage_by_risk(
    artifact: ArtifactBase,
    top_n: int = 10,
) -> list[TriageResult]:
    """Triage artifact items by risk.

    Args:
        artifact: Artifact to triage.
        top_n: Number of top items to return.

    Returns:
        List of TriageResult sorted by risk (highest first).
    """
    results = []

    # Process facts
    for i, fact in enumerate(artifact.facts):
        item = {
            "content": fact.statement,
            "has_evidence": len(fact.evidence_refs) > 0,
            "confidence": fact.confidence,
        }
        risk_score, reasons = calculate_risk_score(item, "fact")
        results.append(
            TriageResult(
                item_id=f"fact_{i}",
                item_type="fact",
                content=fact.statement,
                risk_score=risk_score,
                risk_reasons=reasons,
            )
        )

    # Process inferences
    for i, inf in enumerate(artifact.inferences):
        item = {
            "content": inf.statement,
        }
        risk_score, reasons = calculate_risk_score(item, "inference")
        results.append(
            TriageResult(
                item_id=f"inference_{i}",
                item_type="inference",
                content=inf.statement,
                risk_score=risk_score,
                risk_reasons=reasons,
            )
        )

    # Sort by risk (highest first)
    results.sort(key=lambda x: x.risk_score, reverse=True)

    return results[:top_n]


def generate_triage_report(results: list[TriageResult]) -> str:
    """Generate markdown triage report."""
    lines = [
        "# Triage Report",
        "",
        "Items sorted by risk score (highest first).",
        "",
    ]

    for r in results:
        emoji = "🔴" if r.risk_score > 0.5 else "🟡" if r.risk_score > 0.2 else "🟢"
        lines.append(f"## {emoji} {r.item_id} (Risk: {r.risk_score:.0%})")
        lines.append(f"**Type**: {r.item_type}")
        lines.append(f"**Content**: {r.content[:100]}...")
        if r.risk_reasons:
            lines.append(f"**Reasons**: {', '.join(r.risk_reasons)}")
        lines.append("")

    return "\n".join(lines)
