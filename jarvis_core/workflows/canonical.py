"""Canonical Workflows.

Per V4-C1, these are the standard research workflows.
Each workflow is a complete pipeline from input to artifact output.
"""
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from ..artifacts.schema import ArtifactBase, Provenance, Inference, Recommendation
from ..artifacts.adapters import adapt_to_artifact

if TYPE_CHECKING:
    from ..paper_vector import PaperVector


def run_literature_to_plan(
    vectors: List["PaperVector"],
    focus_concepts: List[str],
    goal: str = "research",
) -> ArtifactBase:
    """Workflow 1: Literature → Research Plan.

    Pipeline: PDF/URL → Evidence → PaperVector → α-γ → PlanArtifact

    Args:
        vectors: Input PaperVectors.
        focus_concepts: Concepts to focus on.
        goal: Research goal description.

    Returns:
        PlanArtifact with research plan.
    """
    from ..gap_analysis import score_research_gaps
    from ..hypothesis import generate_hypotheses
    from ..feasibility import score_feasibility

    if not vectors:
        return ArtifactBase(
            kind="research_plan",
            inferences=[Inference(
                statement="No input vectors provided",
                method="validation",
                confidence=0.0,
            )],
            provenance=Provenance(source_modules=["literature_to_plan"]),
        )

    # Step 1: Gap Analysis
    gaps = []
    for concept in focus_concepts:
        gap_result = score_research_gaps(vectors, concept)
        gaps.extend(gap_result)

    # Step 2: Generate Hypotheses
    hypotheses = generate_hypotheses(vectors, focus_concepts)

    # Step 3: Assess Feasibility
    feasibility_results = []
    for hyp in hypotheses[:3]:
        feas = score_feasibility(hyp["hypothesis"], vectors)
        feasibility_results.append({
            "hypothesis": hyp["hypothesis"],
            "feasibility": feas,
        })

    # Build Artifact
    inferences = [
        Inference(
            statement=f"Gap identified: {g.get('concept', 'unknown')} (score: {g.get('gap_score', 0):.2f})",
            method="gap_analysis",
            confidence=g.get("gap_score", 0.5),
        )
        for g in gaps[:3]
    ]

    for hyp in hypotheses[:3]:
        inferences.append(Inference(
            statement=hyp["hypothesis"],
            method="hypothesis_generation",
            confidence=hyp.get("confidence", 0.5),
        ))

    recommendations = []
    for fr in feasibility_results:
        if fr["feasibility"].get("overall", 0) > 0.4:
            recommendations.append(Recommendation(
                statement=f"Pursue: {fr['hypothesis'][:50]}...",
                rationale=fr["feasibility"].get("reason", "Feasible"),
                priority="high" if fr["feasibility"].get("overall", 0) > 0.6 else "medium",
            ))

    return ArtifactBase(
        kind="research_plan",
        inferences=inferences,
        recommendations=recommendations,
        metrics={
            "gap_count": len(gaps),
            "hypothesis_count": len(hypotheses),
            "feasible_count": len([f for f in feasibility_results if f["feasibility"].get("overall", 0) > 0.4]),
        },
        provenance=Provenance(
            source_modules=["gap_analysis", "hypothesis", "feasibility"],
        ),
        raw_data={
            "gaps": gaps,
            "hypotheses": hypotheses,
            "feasibility": feasibility_results,
        },
    )


def run_plan_to_grant(
    plan_artifact: ArtifactBase,
    vectors: List["PaperVector"],
    grant_keywords: List[str],
) -> ArtifactBase:
    """Workflow 2: Research Plan → Grant Proposal.

    Args:
        plan_artifact: Research plan from workflow 1.
        vectors: Supporting PaperVectors.
        grant_keywords: Keywords from grant call.

    Returns:
        Grant proposal artifact.
    """
    from ..grant_optimizer import optimize_grant_proposal

    result = optimize_grant_proposal(vectors, grant_keywords)
    artifact = adapt_to_artifact("grant_optimizer", result)

    # Enhance with plan info
    if plan_artifact.recommendations:
        artifact.inferences.append(Inference(
            statement=f"Based on {len(plan_artifact.recommendations)} recommended directions",
            method="plan_integration",
            confidence=0.7,
        ))

    artifact.provenance.source_modules.append("plan_to_grant")

    return artifact


def run_plan_to_paper(
    plan_artifact: ArtifactBase,
    vectors: List["PaperVector"],
) -> ArtifactBase:
    """Workflow 3: Research Plan → Paper Structure.

    Pipeline: PlanArtifact → figure planner → logic audit → submission package

    Args:
        plan_artifact: Research plan.
        vectors: Supporting vectors.

    Returns:
        Paper structure artifact.
    """
    from ..sigma_modules import plan_figures
    from ..lambda_modules import check_figure_claim_consistency

    figures = plan_figures(vectors)
    claims = [inf.statement for inf in plan_artifact.inferences]

    consistency = check_figure_claim_consistency(
        [f["description"] for f in figures],
        claims,
    )

    inferences = [
        Inference(
            statement=f"Paper structure with {len(figures)} figures planned",
            method="figure_planning",
            confidence=0.7,
        ),
        Inference(
            statement=f"Figure-claim consistency: {consistency.get('consistency_score', 0):.2f}",
            method="consistency_check",
            confidence=consistency.get("consistency_score", 0.5),
        ),
    ]

    recommendations = [
        Recommendation(
            statement="Complete figure legends before submission",
            rationale="Standard practice",
            priority="high",
        ),
    ]

    return ArtifactBase(
        kind="paper_structure",
        inferences=inferences,
        recommendations=recommendations,
        metrics={"figure_count": len(figures)},
        provenance=Provenance(source_modules=["plan_to_paper", "sigma_modules"]),
        raw_data={"figures": figures, "consistency": consistency},
    )


def run_plan_to_talk(
    plan_artifact: ArtifactBase,
    vectors: List["PaperVector"],
    duration_minutes: int = 15,
) -> ArtifactBase:
    """Workflow 4: Research Plan → Presentation.

    Pipeline: PlanArtifact → rehearsal → slides outline

    Args:
        plan_artifact: Research plan.
        vectors: Supporting vectors.
        duration_minutes: Target talk duration.

    Returns:
        Presentation structure artifact.
    """
    from ..rehearsal import generate_rehearsal

    rehearsal = generate_rehearsal(vectors)

    slides_per_minute = 1
    slide_count = duration_minutes * slides_per_minute

    inferences = [
        Inference(
            statement=f"Presentation structure: {slide_count} slides for {duration_minutes} min",
            method="time_allocation",
            confidence=0.8,
        ),
        Inference(
            statement=f"Prepared {len(rehearsal.get('questions', []))} rehearsal questions",
            method="rehearsal_generation",
            confidence=0.7,
        ),
    ]

    recommendations = []
    for q in rehearsal.get("tough_questions", [])[:3]:
        recommendations.append(Recommendation(
            statement=f"Prepare answer for: {q[:50]}...",
            rationale="Anticipate tough questions",
            priority="high",
        ))

    return ArtifactBase(
        kind="presentation",
        inferences=inferences,
        recommendations=recommendations,
        metrics={
            "slide_count": slide_count,
            "question_count": len(rehearsal.get("questions", [])),
        },
        provenance=Provenance(source_modules=["plan_to_talk", "rehearsal"]),
        raw_data={
            "rehearsal": rehearsal,
            "duration_minutes": duration_minutes,
        },
    )
