"""Phase Ψ-26 to Ψ-30: Meta-Science and Self-Evolution.

Per Research OS v3.0 specification.
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


# Ψ-26: Field Saturation Collapse Predictor
def predict_field_collapse(
    vectors: List["PaperVector"],
    concept: str,
) -> dict:
    """Predict field saturation and potential collapse.

    Args:
        vectors: PaperVectors in the field.
        concept: Concept to analyze.

    Returns:
        Collapse risk assessment.
    """
    if not vectors:
        return {"collapse_risk": 0.0, "estimated": True}

    # Find relevant papers
    relevant = [v for v in vectors if concept.lower() in str(v.concept.concepts).lower()]

    if not relevant:
        return {"collapse_risk": 0.0, "reason": "コンセプト不在", "estimated": True}

    # Check novelty decline
    avg_novelty = sum(v.temporal.novelty for v in relevant) / len(relevant)

    # Check year concentration
    years = [v.metadata.year for v in relevant if v.metadata.year]
    year_spread = max(years) - min(years) if len(years) >= 2 else 0

    # Collapse indicators
    collapse_risk = 0.0
    reasons = []

    if avg_novelty < 0.3:
        collapse_risk += 0.3
        reasons.append("新規性の枯渇")

    if year_spread < 3 and len(relevant) > 5:
        collapse_risk += 0.2
        reasons.append("短期集中の過熱傾向")

    collapse_risk = min(1.0, collapse_risk)

    return {
        "concept": concept,
        "collapse_risk": round(collapse_risk, 2),
        "reasons": reasons if reasons else ["リスク低"],
        "paper_count": len(relevant),
        "estimated": True,
    }


# Ψ-27: Journal Power Shift Tracker
def track_journal_power_shift(
    vectors: List["PaperVector"],
) -> dict:
    """Track journal influence changes.

    Args:
        vectors: PaperVectors to analyze.

    Returns:
        Power shift map.
    """
    if not vectors:
        return {"power_shift_map": {}, "estimated": True}

    # Count by journal and year
    by_journal_year = {}
    for v in vectors:
        journal = v.metadata.journal or "unknown"
        year = v.metadata.year or 0
        if journal not in by_journal_year:
            by_journal_year[journal] = []
        by_journal_year[journal].append(year)

    # Analyze trends
    power_shift_map = {}
    for journal, years in by_journal_year.items():
        if len(years) < 2:
            continue
        avg_year = sum(years) / len(years)
        power_shift_map[journal] = {
            "count": len(years),
            "trend": "rising" if avg_year > 2020 else "stable",
        }

    return {
        "power_shift_map": power_shift_map,
        "total_journals": len(by_journal_year),
        "estimated": True,
    }


# Ψ-28: Citation Cartel Detector
def detect_citation_cartel(
    vectors: List["PaperVector"],
) -> dict:
    """Detect unhealthy citation patterns.

    Args:
        vectors: PaperVectors to analyze.

    Returns:
        Cartel cluster detection.
    """
    # Simplified: detect high concept self-citation
    concept_groups = {}
    for v in vectors:
        for c in v.concept.concepts:
            if c not in concept_groups:
                concept_groups[c] = []
            concept_groups[c].append(v.paper_id)

    cartel_clusters = []
    for concept, papers in concept_groups.items():
        if len(papers) > 5:
            cartel_clusters.append({
                "concept": concept,
                "paper_count": len(papers),
                "risk": "potential echo chamber",
            })

    return {
        "cartel_clusters": cartel_clusters[:5],
        "healthy": len(cartel_clusters) == 0,
        "estimated": True,
    }


# Ψ-29: Meta-Science Observatory
def observe_meta_science(
    vectors: List["PaperVector"],
) -> dict:
    """Observe academic system metrics.

    Args:
        vectors: PaperVectors as sample.

    Returns:
        System-level metrics.
    """
    if not vectors:
        return {"system_metrics": {}, "estimated": True}

    # Calculate system metrics
    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
    avg_impact = sum(v.impact.future_potential for v in vectors) / len(vectors)

    methods = set()
    concepts = set()
    for v in vectors:
        methods.update(v.method.methods.keys())
        concepts.update(v.concept.concepts.keys())

    return {
        "system_metrics": {
            "avg_novelty": round(avg_novelty, 2),
            "avg_impact": round(avg_impact, 2),
            "method_diversity": len(methods),
            "concept_diversity": len(concepts),
            "total_papers": len(vectors),
        },
        "health_score": round((avg_novelty + avg_impact) / 2, 2),
        "estimated": True,
    }


# Ψ-30: Research OS Self-Evolution Engine
def suggest_self_evolution(
    vectors: List["PaperVector"],
    current_features: List[str],
) -> dict:
    """Suggest next features for Research OS.

    Args:
        vectors: Context vectors.
        current_features: List of current features.

    Returns:
        Feature candidates for next version.
    """
    # Analyze usage patterns (simulated)
    next_feature_candidates = [
        "自動仮説生成の精度向上",
        "リアルタイムパラダイムシフト検出",
        "個人化された研究戦略AI",
        "多言語論文統合分析",
        "共同研究者マッチング",
    ]

    # Prioritize based on current gaps
    priorities = []
    if "hypothesis" not in str(current_features).lower():
        priorities.append(next_feature_candidates[0])
    if "paradigm" not in str(current_features).lower():
        priorities.append(next_feature_candidates[1])

    return {
        "next_feature_candidates": next_feature_candidates,
        "priority_features": priorities if priorities else next_feature_candidates[:2],
        "current_feature_count": len(current_features),
        "estimated": True,
    }
