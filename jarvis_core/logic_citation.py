"""Phase Ψ-11 to Ψ-15: Logic and Citation Engines.

Per Research OS v3.0 specification.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


# Ψ-11: Argument Map Generator
def generate_argument_map(claims: list[str]) -> dict:
    """Generate argument structure graph.

    Args:
        claims: List of claims to map.

    Returns:
        Argument map with nodes and edges.
    """
    if not claims:
        return {"nodes": [], "edges": []}

    nodes = [{"id": i, "claim": c[:50], "type": "claim"} for i, c in enumerate(claims)]
    edges = []

    # Connect sequential claims
    for i in range(len(claims) - 1):
        edges.append({"from": i, "to": i + 1, "relation": "supports"})

    return {"nodes": nodes, "edges": edges, "total_claims": len(claims)}


# Ψ-12: Scientific Controversy Tracker
def track_controversies(
    vectors: list[PaperVector],
) -> list[dict]:
    """Track scientific controversies in a field.

    Args:
        vectors: PaperVectors to analyze.

    Returns:
        List of controversy dicts.
    """
    if not vectors:
        return []

    controversies = []

    # Find papers with opposing biological axes
    high_immune = [v for v in vectors if v.biological_axis.immune_activation > 0.3]
    low_immune = [v for v in vectors if v.biological_axis.immune_activation < -0.3]

    if high_immune and low_immune:
        controversies.append(
            {
                "topic": "免疫活性化 vs 抑制",
                "pro_papers": len(high_immune),
                "con_papers": len(low_immune),
                "status": "ongoing",
            }
        )

    return controversies


# Ψ-13: Claim Confidence Index
def calculate_claim_confidence(
    claim: str,
    vectors: list[PaperVector],
) -> dict:
    """Calculate confidence index for a claim.

    Args:
        claim: The claim to evaluate.
        vectors: Supporting vectors.

    Returns:
        Confidence assessment.
    """
    if not claim or not vectors:
        return {"confidence_index": 0.0, "estimated": True}

    # Count supporting evidence
    claim_lower = claim.lower()
    supporting = sum(1 for v in vectors for c in v.concept.concepts if c.lower() in claim_lower)

    # Base confidence on support count
    confidence = min(1.0, supporting / max(len(vectors), 1))

    return {
        "claim": claim[:50],
        "confidence_index": round(confidence, 2),
        "supporting_count": supporting,
        "total_papers": len(vectors),
        "estimated": True,
    }


# Ψ-14: Citation Power Index
def calculate_citation_power(
    vectors: list[PaperVector],
) -> dict:
    """Calculate citation power index.

    Args:
        vectors: PaperVectors to evaluate.

    Returns:
        Citation power analysis.
    """
    if not vectors:
        return {"citation_strength": 0.0, "estimated": True}

    # Use impact as proxy for citations
    total_impact = sum(v.impact.future_potential for v in vectors)
    avg_impact = total_impact / len(vectors)

    # Calculate strength based on impact distribution
    citation_strength = round(avg_impact, 2)

    return {
        "citation_strength": citation_strength,
        "total_papers": len(vectors),
        "high_impact_count": sum(1 for v in vectors if v.impact.future_potential > 0.6),
        "estimated": True,
    }


# Ψ-15: Paper Longevity Predictor
def predict_paper_longevity(
    vector: PaperVector,
) -> dict:
    """Predict how long a paper will remain relevant.

    Args:
        vector: The PaperVector to evaluate.

    Returns:
        Longevity prediction.
    """
    # Base survival on novelty and impact
    novelty = vector.temporal.novelty
    impact = vector.impact.future_potential

    # Higher novelty = longer relevance
    base_years = 5
    novelty_bonus = int(novelty * 10)
    impact_bonus = int(impact * 5)

    predicted_years = base_years + novelty_bonus + impact_bonus
    survival_probability = min(1.0, (novelty + impact) / 2)

    return {
        "paper_id": vector.paper_id,
        "survival_probability": round(survival_probability, 2),
        "predicted_relevance_years": predicted_years,
        "estimated": True,
    }
