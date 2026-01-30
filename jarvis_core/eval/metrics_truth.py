"""Truth Metrics.

Per V4-A03, this calculates truth-related metrics:
- 誤FACT率 (Unsupported FACT rate)
- 降格率 (Downgrade rate)
- 矛盾検出精度 (Contradiction detection accuracy)
- 引用関連性P/R (Citation relevance precision/recall)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..artifacts.schema import ArtifactBase
    from .goldset_schema import GoldsetEntry


@dataclass
class TruthMetrics:
    """Truth metrics result."""

    # Core metrics
    unsupported_fact_rate: float  # 誤FACT率
    downgrade_rate: float  # 降格率
    fact_precision: float  # Precision for FACT labels
    fact_recall: float  # Recall for FACT labels

    # Detail counts
    total_claims: int
    facts_with_evidence: int
    facts_without_evidence: int
    inferences: int
    unsupported: int

    # Flags
    flags: list[str]

    def to_dict(self) -> dict:
        return {
            "unsupported_fact_rate": round(self.unsupported_fact_rate, 4),
            "downgrade_rate": round(self.downgrade_rate, 4),
            "fact_precision": round(self.fact_precision, 4),
            "fact_recall": round(self.fact_recall, 4),
            "total_claims": self.total_claims,
            "facts_with_evidence": self.facts_with_evidence,
            "facts_without_evidence": self.facts_without_evidence,
            "inferences": self.inferences,
            "unsupported": self.unsupported,
            "flags": self.flags,
        }

    def is_passing(self, max_unsupported_rate: float = 0.1) -> bool:
        """Check if metrics pass quality gate."""
        return self.unsupported_fact_rate <= max_unsupported_rate


def calculate_truth_metrics(
    predictions: list[dict],
    goldset: list[GoldsetEntry] = None,
) -> TruthMetrics:
    """Calculate truth metrics.

    Args:
        predictions: List of prediction dicts with 'claim', 'label', 'has_evidence'.
        goldset: Optional goldset for comparison.

    Returns:
        TruthMetrics with calculated values.
    """
    if not predictions:
        return TruthMetrics(
            unsupported_fact_rate=0.0,
            downgrade_rate=0.0,
            fact_precision=1.0,
            fact_recall=1.0,
            total_claims=0,
            facts_with_evidence=0,
            facts_without_evidence=0,
            inferences=0,
            unsupported=0,
            flags=[],
        )

    total = len(predictions)
    facts_with_evidence = 0
    facts_without_evidence = 0
    inferences = 0
    unsupported = 0
    downgraded = 0
    flags = []

    for pred in predictions:
        label = pred.get("label", "unknown")
        has_evidence = pred.get("has_evidence", False)

        if label == "fact":
            if has_evidence:
                facts_with_evidence += 1
            else:
                facts_without_evidence += 1
                flags.append(f"FACT without evidence: {pred.get('claim', '')[:50]}")
        elif label == "inference":
            inferences += 1
            if pred.get("was_downgraded", False):
                downgraded += 1
        elif label == "unsupported":
            unsupported += 1

    # Calculate rates
    unsupported_fact_rate = facts_without_evidence / total if total > 0 else 0
    downgrade_rate = downgraded / total if total > 0 else 0

    # Calculate precision/recall against goldset if provided
    precision = 1.0
    recall = 1.0

    if goldset:
        from .goldset_schema import GoldsetLabel

        gold_facts = {e.claim_id for e in goldset if e.expected_label == GoldsetLabel.FACT}
        pred_facts = {p.get("claim_id") for p in predictions if p.get("label") == "fact"}

        if pred_facts:
            true_positives = len(gold_facts & pred_facts)
            precision = true_positives / len(pred_facts)
        if gold_facts:
            true_positives = len(gold_facts & pred_facts)
            recall = true_positives / len(gold_facts)

    return TruthMetrics(
        unsupported_fact_rate=unsupported_fact_rate,
        downgrade_rate=downgrade_rate,
        fact_precision=precision,
        fact_recall=recall,
        total_claims=total,
        facts_with_evidence=facts_with_evidence,
        facts_without_evidence=facts_without_evidence,
        inferences=inferences,
        unsupported=unsupported,
        flags=flags,
    )


def calculate_artifact_metrics(artifact: ArtifactBase) -> TruthMetrics:
    """Calculate metrics from an artifact."""
    predictions = []

    for fact in artifact.facts:
        predictions.append(
            {
                "claim": fact.statement,
                "label": "fact",
                "has_evidence": len(fact.evidence_refs) > 0,
            }
        )

    for inf in artifact.inferences:
        predictions.append(
            {
                "claim": inf.statement,
                "label": "inference",
                "has_evidence": False,
                "was_downgraded": "降格" in inf.statement or "downgrade" in inf.method,
            }
        )

    return calculate_truth_metrics(predictions)