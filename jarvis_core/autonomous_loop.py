"""Autonomous Research Loop.

Per Issue Ω-1, this implements self-driving research cycles:
PaperVector → Gap → Hypothesis → Experiment → Re-evaluation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


@dataclass
class LoopIteration:
    """One iteration of the research loop."""

    iteration: int
    gap_analysis: dict
    hypotheses: list[dict]
    experiments: list[dict]
    evaluation: dict
    human_intervention_points: list[str]


@dataclass
class ResearchLoopResult:
    """Result of autonomous research loop."""

    iterations: list[LoopIteration]
    final_recommendations: list[str]
    convergence_achieved: bool
    total_hypotheses_generated: int
    total_experiments_proposed: int
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None


def run_autonomous_research_loop(
    vectors: list[PaperVector],
    focus_concepts: list[str],
    max_iterations: int = 3,
) -> dict:
    """Run autonomous research loop.

    Cycles through: Gap Analysis → Hypothesis → Experiment → Re-evaluate

    Args:
        vectors: PaperVectors as knowledge base.
        focus_concepts: Concepts to focus on.
        max_iterations: Maximum loop iterations.

    Returns:
        Loop result dict with all iterations.
    """
    from .feasibility import score_feasibility
    from .gap_analysis import score_research_gaps
    from .hypothesis import generate_hypotheses

    if not vectors or not focus_concepts:
        return {
            "iterations": [],
            "status": "no_input",
            "convergence": False,
        }

    iterations = []
    all_hypotheses = []
    all_experiments = []

    for i in range(max_iterations):
        # Step 1: Gap Analysis
        gap_results = []
        for concept in focus_concepts:
            gaps = score_research_gaps(vectors, concept)
            gap_results.extend(gaps)

        # Sort by gap score
        gap_results.sort(key=lambda x: x.get("gap_score", 0), reverse=True)
        top_gaps = gap_results[:3]

        # Step 2: Generate Hypotheses
        hypotheses = generate_hypotheses(
            vectors,
            [g["concept"] for g in top_gaps],
        )
        all_hypotheses.extend(hypotheses)

        # Step 3: Design Experiments
        experiments = []
        for hyp in hypotheses[:2]:
            feasibility = score_feasibility(hyp["hypothesis"], vectors)
            experiments.append(
                {
                    "hypothesis": hyp["hypothesis"],
                    "feasibility": feasibility,
                    "proposed_methods": hyp.get("based_on", []),
                }
            )
        all_experiments.extend(experiments)

        # Step 4: Evaluate
        avg_feasibility = 0.0
        if experiments:
            avg_feasibility = sum(e["feasibility"].get("overall", 0.5) for e in experiments) / len(
                experiments
            )

        evaluation = {
            "avg_feasibility": round(avg_feasibility, 3),
            "gaps_remaining": len([g for g in gap_results if g.get("gap_score", 0) > 0.5]),
            "iteration": i + 1,
        }

        # Human intervention points
        intervention_points = []
        if avg_feasibility < 0.4:
            intervention_points.append("実験難度が高い - 代替アプローチの検討を推奨")
        if len(hypotheses) > 5:
            intervention_points.append("仮説が多数 - 優先順位付けが必要")
        if i == max_iterations - 1:
            intervention_points.append("最終イテレーション - 実行判断が必要")

        iteration = LoopIteration(
            iteration=i + 1,
            gap_analysis={"top_gaps": top_gaps},
            hypotheses=hypotheses,
            experiments=experiments,
            evaluation=evaluation,
            human_intervention_points=intervention_points,
        )
        iterations.append(iteration)

        # Check convergence
        if evaluation["gaps_remaining"] == 0:
            break

    # Final recommendations
    recommendations = []
    if all_hypotheses:
        recommendations.append(f"最有望仮説: {all_hypotheses[0]['hypothesis'][:50]}...")
    if all_experiments:
        best_exp = max(all_experiments, key=lambda x: x["feasibility"].get("overall", 0))
        recommendations.append(f"推奨実験: {best_exp['hypothesis'][:30]}...")

    return {
        "iterations": [
            {
                "iteration": it.iteration,
                "gap_analysis": it.gap_analysis,
                "hypotheses": it.hypotheses,
                "experiments": it.experiments,
                "evaluation": it.evaluation,
                "human_intervention_points": it.human_intervention_points,
            }
            for it in iterations
        ],
        "final_recommendations": recommendations,
        "convergence": iterations[-1].evaluation["gaps_remaining"] == 0 if iterations else False,
        "total_hypotheses": len(all_hypotheses),
        "total_experiments": len(all_experiments),
        "status": "completed",
    }


def get_intervention_summary(loop_result: dict) -> str:
    """Get human intervention summary."""
    all_points = []
    for it in loop_result.get("iterations", []):
        for point in it.get("human_intervention_points", []):
            all_points.append(f"[Iter {it['iteration']}] {point}")

    if not all_points:
        return "人間介入不要"

    return "\n".join(all_points)