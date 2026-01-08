"""Phase Ψ-16 to Ψ-20: Thinking Limit Breakthrough Engines.

Per Research OS v3.0 specification.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


# Ψ-16: Counterfactual Research Engine
def analyze_counterfactual(
    vector: PaperVector,
    all_vectors: list[PaperVector],
) -> dict:
    """Analyze 'what if this paper didn't exist' impact.

    Args:
        vector: The paper to hypothetically remove.
        all_vectors: All papers in the field.

    Returns:
        Counterfactual impact analysis.
    """
    if not all_vectors:
        return {"impact_delta": 0.0, "estimated": True}

    # Find papers that would be affected
    concept_overlap = set(vector.concept.concepts.keys())
    affected = [
        v for v in all_vectors
        if v.paper_id != vector.paper_id
        and any(c in v.concept.concepts for c in concept_overlap)
    ]

    # Calculate impact delta
    impact_delta = vector.impact.future_potential * (len(affected) / max(len(all_vectors), 1))

    return {
        "paper_id": vector.paper_id,
        "impact_delta": round(impact_delta, 2),
        "affected_papers": len(affected),
        "interpretation": "高い影響力" if impact_delta > 0.3 else "限定的な影響",
        "estimated": True,
    }


# Ψ-17: Blind-Spot Discovery Engine
def discover_blind_spots(
    vectors: list[PaperVector],
) -> list[dict]:
    """Discover collective blind spots in research.

    Args:
        vectors: PaperVectors to analyze.

    Returns:
        List of blind spots.
    """
    if not vectors:
        return []

    blind_spots = []

    # Check axis coverage
    immune_coverage = sum(abs(v.biological_axis.immune_activation) for v in vectors) / len(vectors)
    metab_coverage = sum(abs(v.biological_axis.metabolism_signal) for v in vectors) / len(vectors)
    tumor_coverage = sum(abs(v.biological_axis.tumor_context) for v in vectors) / len(vectors)

    if immune_coverage < 0.3:
        blind_spots.append({
            "axis": "immune",
            "gap": "免疫軸の研究不足",
            "severity": round(1 - immune_coverage, 2),
        })

    if metab_coverage < 0.3:
        blind_spots.append({
            "axis": "metabolism",
            "gap": "代謝軸の研究不足",
            "severity": round(1 - metab_coverage, 2),
        })

    if tumor_coverage < 0.3:
        blind_spots.append({
            "axis": "tumor",
            "gap": "腫瘍文脈の研究不足",
            "severity": round(1 - tumor_coverage, 2),
        })

    return blind_spots


# Ψ-18: Concept Mutation Simulator
def simulate_concept_mutation(
    concept: str,
    vectors: list[PaperVector],
) -> dict:
    """Simulate how a concept might evolve across fields.

    Args:
        concept: Concept to simulate.
        vectors: Context vectors.

    Returns:
        Mutation path predictions.
    """
    mutation_paths = []

    # Find related concepts
    related = set()
    for v in vectors:
        if concept in v.concept.concepts:
            related.update(v.concept.concepts.keys())

    related.discard(concept)

    for r in list(related)[:5]:
        mutation_paths.append({
            "from": concept,
            "to": f"{concept}×{r}",
            "probability": 0.3,
            "field": "cross-disciplinary",
        })

    return {
        "original_concept": concept,
        "mutation_paths": mutation_paths,
        "evolution_potential": len(mutation_paths) / 5,
        "estimated": True,
    }


# Ψ-19: AI-vs-AI Research Debate
def simulate_research_debate(
    hypothesis: str,
    vectors: list[PaperVector],
) -> dict:
    """Simulate AI debate on research strategy.

    Args:
        hypothesis: Hypothesis to debate.
        vectors: Context vectors.

    Returns:
        Debate transcript and conclusion.
    """
    # Pro arguments
    pro_args = [
        f"{hypothesis}は新規性が高い",
        "関連研究のギャップを埋める",
    ]

    # Con arguments
    con_args = [
        "再現性の担保が困難",
        "実験系の確立に時間がかかる",
    ]

    # Determine winner based on evidence
    supporting = sum(1 for v in vectors for c in v.concept.concepts if c.lower() in hypothesis.lower())
    winner = "pro" if supporting > len(vectors) / 2 else "con"

    return {
        "hypothesis": hypothesis[:50],
        "pro_arguments": pro_args,
        "con_arguments": con_args,
        "winner": winner,
        "conclusion": "追求推奨" if winner == "pro" else "再検討推奨",
        "estimated": True,
    }


# Ψ-20: Hypothesis Darwinism Engine
def simulate_hypothesis_evolution(
    hypotheses: list[str],
    vectors: list[PaperVector],
    generations: int = 3,
) -> dict:
    """Simulate hypothesis survival across generations.

    Args:
        hypotheses: Initial hypotheses.
        vectors: Context vectors.
        generations: Number of generations.

    Returns:
        Surviving hypotheses.
    """
    if not hypotheses:
        return {"surviving_hypotheses": [], "estimated": True}

    # Score each hypothesis
    scored = []
    for h in hypotheses:
        h_lower = h.lower()
        support = sum(1 for v in vectors for c in v.concept.concepts if c.lower() in h_lower)
        scored.append((h, support / max(len(vectors), 1)))

    # Select survivors (top half)
    scored.sort(key=lambda x: x[1], reverse=True)
    survivors = [s[0] for s in scored[:max(1, len(scored) // 2)]]

    return {
        "initial_count": len(hypotheses),
        "surviving_hypotheses": survivors,
        "survival_rate": round(len(survivors) / len(hypotheses), 2),
        "generations": generations,
        "estimated": True,
    }
