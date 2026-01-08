"""Phase Ψ-21 to Ψ-25: Research Career Engines.

Per Research OS v3.0 specification.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


# Ψ-21: Burnout Risk Monitor
def monitor_burnout_risk(
    vectors: list[PaperVector],
    hours_per_week: float = 50,
    months_at_pace: int = 12,
) -> dict:
    """Monitor burnout risk from research patterns.

    Args:
        vectors: PaperVectors representing workload.
        hours_per_week: Weekly working hours.
        months_at_pace: Duration at current pace.

    Returns:
        Burnout risk assessment.
    """
    # Base risk on workload intensity
    workload_risk = min(1.0, hours_per_week / 70)
    duration_risk = min(1.0, months_at_pace / 24)

    # Check output pressure (many papers = high pressure)
    output_pressure = min(1.0, len(vectors) / 10) if vectors else 0.3

    burnout_risk = (workload_risk + duration_risk + output_pressure) / 3

    recommendations = []
    if burnout_risk > 0.6:
        recommendations.append("休息の優先")
        recommendations.append("タスクの委譲検討")
    elif burnout_risk > 0.3:
        recommendations.append("ペース調整を推奨")

    return {
        "burnout_risk": round(burnout_risk, 2),
        "workload_factor": round(workload_risk, 2),
        "duration_factor": round(duration_risk, 2),
        "recommendations": recommendations if recommendations else ["現状維持可能"],
        "estimated": True,
    }


# Ψ-22: Skill Gap Evolution Tracker
def track_skill_gap(
    vectors: list[PaperVector],
    target_skills: list[str],
) -> dict:
    """Track skill gaps over time.

    Args:
        vectors: PaperVectors representing experience.
        target_skills: Skills to achieve.

    Returns:
        Skill gap timeline.
    """
    if not target_skills:
        return {"skill_gap_timeline": [], "estimated": True}

    # Current skills from methods
    current_skills = set()
    for v in vectors:
        current_skills.update(v.method.methods.keys())

    # Find gaps
    gaps = [s for s in target_skills if s not in current_skills]

    timeline = []
    for skill in gaps:
        timeline.append({
            "skill": skill,
            "status": "missing",
            "priority": "high" if skill == gaps[0] else "medium",
            "suggested_action": f"{skill}のトレーニング/共同研究",
        })

    return {
        "skill_gap_timeline": timeline,
        "current_skills": list(current_skills)[:10],
        "gap_count": len(gaps),
        "estimated": True,
    }


# Ψ-23: Mentorship Matching Engine
def suggest_mentor_profile(
    vectors: list[PaperVector],
    career_goal: str = "pi",
) -> dict:
    """Suggest ideal mentor profile.

    Args:
        vectors: Mentee's PaperVectors.
        career_goal: Career goal (phd, postdoc, pi).

    Returns:
        Mentor profile suggestion.
    """
    # Analyze mentee's needs
    needs = []

    if vectors:
        methods = set()
        for v in vectors:
            methods.update(v.method.methods.keys())

        if len(methods) < 3:
            needs.append("技術指導")

        avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
        if avg_novelty < 0.5:
            needs.append("独創性開発")

    mentor_profile = {
        "expertise": "complementary" if needs else "similar",
        "style": "hands-on" if "技術指導" in needs else "strategic",
        "network": "strong" if career_goal == "pi" else "growing",
        "needs_addressed": needs,
    }

    return {
        "mentor_profile": mentor_profile,
        "career_goal": career_goal,
        "estimated": True,
    }


# Ψ-24: International Mobility Planner
def plan_international_mobility(
    vectors: list[PaperVector],
    target_region: str = "us",
) -> dict:
    """Plan international research mobility.

    Args:
        vectors: Current research portfolio.
        target_region: Target region (us, eu, asia).

    Returns:
        Mobility plan.
    """
    # Analyze competitiveness
    competitiveness = 0.5
    if vectors:
        avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
        avg_impact = sum(v.impact.future_potential for v in vectors) / len(vectors)
        competitiveness = (avg_novelty + avg_impact) / 2

    plan = {
        "target_region": target_region,
        "competitiveness_score": round(competitiveness, 2),
        "preparation_steps": [
            "英語論文の増強" if competitiveness < 0.6 else "ネットワーキング強化",
            "ターゲットラボリストの作成",
            "ファンディング調査",
        ],
        "timeline_months": 12 if competitiveness > 0.6 else 18,
        "estimated": True,
    }

    return plan


# Ψ-25: Reputation Trajectory Simulator
def simulate_reputation_trajectory(
    vectors: list[PaperVector],
    years_ahead: int = 5,
) -> dict:
    """Simulate reputation trajectory.

    Args:
        vectors: Current publication record.
        years_ahead: Years to project.

    Returns:
        Reputation curve projection.
    """
    if not vectors:
        return {"reputation_curve": [], "estimated": True}

    # Current reputation
    current = sum(v.impact.future_potential for v in vectors) / len(vectors)

    # Project growth
    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
    growth_rate = 0.1 * avg_novelty

    curve = []
    rep = current
    for year in range(years_ahead + 1):
        curve.append({
            "year": year,
            "reputation": round(min(1.0, rep), 2),
        })
        rep += growth_rate

    return {
        "reputation_curve": curve,
        "current_reputation": round(current, 2),
        "growth_rate": round(growth_rate, 3),
        "estimated": True,
    }
