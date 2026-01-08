"""Module Adapter Layer.

Per V4-A2, this adapts existing modules to v4.0 Artifact contract
without breaking backward compatibility.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .schema import (
    ArtifactBase,
    Inference,
    Provenance,
    Recommendation,
)

if TYPE_CHECKING:
    pass


def adapt_gap_analysis(result: dict) -> ArtifactBase:
    """Adapt gap_analysis output to Artifact."""
    inferences = [
        Inference(
            statement=f"Research gap detected for {result.get('concept', 'unknown')}",
            method="gap_scoring_heuristic",
            confidence=result.get("gap_score", 0.5),
            supporting_facts=[f"Density: {result.get('density', 0)}"],
        )
    ]

    recommendations = []
    if result.get("gap_score", 0) > 0.5:
        recommendations.append(Recommendation(
            statement=f"Pursue research in {result.get('concept')}",
            rationale=result.get("reason", "High gap score"),
            priority="high" if result.get("gap_score", 0) > 0.7 else "medium",
        ))

    return ArtifactBase(
        kind="gap_analysis",
        inferences=inferences,
        recommendations=recommendations,
        metrics={
            "gap_score": result.get("gap_score", 0),
            "density": result.get("density", 0),
            "novelty": result.get("novelty", 0),
        },
        provenance=Provenance(source_modules=["gap_analysis"]),
        raw_data=result,
    )


def adapt_hypothesis(result: dict) -> ArtifactBase:
    """Adapt hypothesis generation output to Artifact."""
    inferences = [
        Inference(
            statement=result.get("hypothesis", ""),
            method="hypothesis_generation",
            confidence=result.get("confidence", 0.5),
        )
    ]

    return ArtifactBase(
        kind="hypothesis",
        inferences=inferences,
        metrics={"confidence": result.get("confidence", 0.5)},
        provenance=Provenance(source_modules=["hypothesis"]),
        raw_data=result,
    )


def adapt_recommendation(result: dict) -> ArtifactBase:
    """Adapt recommendation engine output to Artifact."""
    inferences = []
    recommendations = []

    for paper in result if isinstance(result, list) else [result]:
        inferences.append(Inference(
            statement=f"Paper {paper.get('paper_id', 'unknown')} is relevant",
            method="concept_similarity_scoring",
            confidence=paper.get("score", 0.5),
        ))
        if paper.get("score", 0) > 0.6:
            recommendations.append(Recommendation(
                statement=f"Review {paper.get('paper_id')}",
                rationale=paper.get("reason", "High relevance score"),
            ))

    return ArtifactBase(
        kind="paper_recommendation",
        inferences=inferences,
        recommendations=recommendations,
        provenance=Provenance(source_modules=["recommendation"]),
        raw_data=result if isinstance(result, dict) else {"papers": result},
    )


def adapt_roi(result: dict) -> ArtifactBase:
    """Adapt ROI engine output to Artifact."""
    return ArtifactBase(
        kind="research_roi",
        inferences=[
            Inference(
                statement=f"ROI Score: {result.get('roi_score', 0)}",
                method="roi_calculation",
                confidence=0.6,
            )
        ],
        recommendations=[
            Recommendation(
                statement=result.get("reason", ""),
                rationale=f"Opportunity cost: {result.get('opportunity_cost', 'unknown')}",
            )
        ],
        metrics={"roi_score": result.get("roi_score", 0)},
        provenance=Provenance(source_modules=["roi_engine"]),
        raw_data=result,
    )


def adapt_feasibility(result: dict) -> ArtifactBase:
    """Adapt feasibility scorer output to Artifact."""
    return ArtifactBase(
        kind="experiment_feasibility",
        inferences=[
            Inference(
                statement=result.get("reason", "Feasibility assessed"),
                method="feasibility_heuristic",
                confidence=result.get("overall", 0.5),
            )
        ],
        metrics={
            "difficulty": result.get("difficulty", 0.5),
            "cost": result.get("cost", 0.5),
            "reproducibility": result.get("reproducibility", 0.5),
            "overall": result.get("overall", 0.5),
        },
        provenance=Provenance(source_modules=["feasibility"]),
        raw_data=result,
    )


def adapt_grant_optimizer(result: dict) -> ArtifactBase:
    """Adapt grant optimizer output to Artifact."""
    recommendations = []
    for risk in result.get("risks", []):
        recommendations.append(Recommendation(
            statement=f"Address: {risk}",
            rationale="Risk mitigation",
            priority="high",
        ))

    return ArtifactBase(
        kind="grant_optimization",
        inferences=[
            Inference(
                statement=result.get("reason", "Grant assessed"),
                method="grant_scoring",
                confidence=result.get("score", 0.5),
            )
        ],
        recommendations=recommendations,
        metrics={
            "score": result.get("score", 0),
            "alignment": result.get("alignment", 0),
            "novelty": result.get("novelty", 0),
        },
        provenance=Provenance(source_modules=["grant_optimizer"]),
        raw_data=result,
    )


# Adapter registry
ADAPTERS = {
    "gap_analysis": adapt_gap_analysis,
    "hypothesis": adapt_hypothesis,
    "recommendation": adapt_recommendation,
    "roi": adapt_roi,
    "feasibility": adapt_feasibility,
    "grant_optimizer": adapt_grant_optimizer,
}


def adapt_to_artifact(module_name: str, result: Any) -> ArtifactBase:
    """Adapt any module output to Artifact.

    Args:
        module_name: Name of the source module.
        result: Raw output from the module.

    Returns:
        ArtifactBase conforming to v4.0 contract.
    """
    adapter = ADAPTERS.get(module_name)
    if adapter:
        return adapter(result)

    # Generic fallback
    return ArtifactBase(
        kind=module_name,
        inferences=[
            Inference(
                statement=f"Result from {module_name}",
                method="generic_adapter",
                confidence=0.5,
            )
        ],
        provenance=Provenance(source_modules=[module_name]),
        raw_data=result if isinstance(result, dict) else {"result": result},
    )
