"""Extended Evaluation Metrics.

Per RP-29, adds fact/inference separation and evidence density metrics.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..artifacts import ClaimSet, ClaimType


@dataclass
class ExtendedMetrics:
    """Extended evaluation metrics."""

    total_claims: int
    fact_count: int
    inference_count: int
    separation_rate: float  # fact_count / total
    evidence_density: float  # citations / claims
    fact_citation_rate: float  # facts with citations / facts
    inference_citation_rate: float  # inferences with citations / inferences


def compute_extended_metrics(claimset: ClaimSet) -> ExtendedMetrics:
    """Compute extended metrics from ClaimSet.

    Per RP-29:
    - separation_rate: proportion of claims properly typed
    - evidence_density: average citations per claim
    - fact_citation_rate: facts with at least 1 citation
    """
    if not claimset.claims:
        return ExtendedMetrics(
            total_claims=0,
            fact_count=0,
            inference_count=0,
            separation_rate=0.0,
            evidence_density=0.0,
            fact_citation_rate=0.0,
            inference_citation_rate=0.0,
        )

    total = len(claimset.claims)
    facts = [c for c in claimset.claims if c.claim_type == ClaimType.FACT]
    inferences = [c for c in claimset.claims if c.claim_type == ClaimType.INFERENCE]

    fact_count = len(facts)
    inference_count = len(inferences)

    # Separation rate: how well claims are typed
    separation_rate = (fact_count + inference_count) / total

    # Evidence density: total citations / claims
    total_citations = sum(len(c.citations) for c in claimset.claims)
    evidence_density = total_citations / total

    # Fact citation rate
    facts_with_citations = sum(1 for c in facts if c.citations)
    fact_citation_rate = facts_with_citations / fact_count if fact_count > 0 else 0.0

    # Inference citation rate
    inferences_with_citations = sum(1 for c in inferences if c.citations)
    inference_citation_rate = (
        inferences_with_citations / inference_count if inference_count > 0 else 0.0
    )

    return ExtendedMetrics(
        total_claims=total,
        fact_count=fact_count,
        inference_count=inference_count,
        separation_rate=separation_rate,
        evidence_density=evidence_density,
        fact_citation_rate=fact_citation_rate,
        inference_citation_rate=inference_citation_rate,
    )


def check_metrics_thresholds(
    metrics: ExtendedMetrics,
    thresholds: dict,
) -> tuple[bool, list[str]]:
    """Check if metrics meet thresholds.

    Returns:
        (pass, failing_gates)
    """
    failing = []

    if "separation_rate" in thresholds:
        if metrics.separation_rate < thresholds["separation_rate"]:
            failing.append(
                f"separation_rate: {metrics.separation_rate:.2f} < {thresholds['separation_rate']}"
            )

    if "evidence_density" in thresholds:
        if metrics.evidence_density < thresholds["evidence_density"]:
            failing.append(
                f"evidence_density: {metrics.evidence_density:.2f} < {thresholds['evidence_density']}"
            )

    if "fact_citation_rate" in thresholds:
        if metrics.fact_citation_rate < thresholds["fact_citation_rate"]:
            failing.append(
                f"fact_citation_rate: {metrics.fact_citation_rate:.2f} < {thresholds['fact_citation_rate']}"
            )

    return len(failing) == 0, failing