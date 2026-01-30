"""Paper Scorer.

Per RP-125, ranks papers with explainable features.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PaperFeatures:
    """Features for paper scoring."""

    paper_id: str
    citation_density: float  # Citations per claim
    recency: float  # 0-1, higher = more recent
    entity_coverage: float  # Ratio of query entities covered
    study_type_hint: str  # review, original, meta-analysis
    evidence_count: int


@dataclass
class PaperScore:
    """Scored paper with breakdown."""

    paper_id: str
    total_score: float
    features: PaperFeatures
    feature_contributions: dict[str, float]
    rank: int = 0


# Feature weights
DEFAULT_WEIGHTS = {
    "citation_density": 0.25,
    "recency": 0.20,
    "entity_coverage": 0.35,
    "study_type": 0.20,
}

# Study type scores
STUDY_TYPE_SCORES = {
    "meta-analysis": 1.0,
    "systematic-review": 0.9,
    "review": 0.7,
    "original": 0.5,
    "case-study": 0.3,
    "unknown": 0.4,
}


def compute_recency(year: int | None, current_year: int = None) -> float:
    """Compute recency score (0-1)."""
    if year is None:
        return 0.5

    if current_year is None:
        current_year = datetime.now().year

    age = current_year - year
    if age <= 0:
        return 1.0
    elif age >= 10:
        return 0.1
    else:
        return 1.0 - (age * 0.09)


def compute_citation_density(
    citation_count: int,
    claim_count: int,
) -> float:
    """Compute citation density score."""
    if claim_count == 0:
        return 0.0

    density = citation_count / claim_count

    # Normalize to 0-1 (2+ citations per claim = 1.0)
    return min(1.0, density / 2.0)


def compute_entity_coverage(
    found_entities: list[str],
    query_entities: list[str],
) -> float:
    """Compute entity coverage score."""
    if not query_entities:
        return 0.5

    found_set = set(e.lower() for e in found_entities)
    query_set = set(e.lower() for e in query_entities)

    if not query_set:
        return 0.5

    return len(found_set & query_set) / len(query_set)


def score_paper(
    features: PaperFeatures,
    weights: dict[str, float] | None = None,
) -> PaperScore:
    """Score a paper based on features.

    Args:
        features: Paper features.
        weights: Optional custom weights.

    Returns:
        PaperScore with total and breakdown.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    contributions = {}

    # Citation density
    contributions["citation_density"] = features.citation_density * weights.get(
        "citation_density", 0.25
    )

    # Recency
    contributions["recency"] = features.recency * weights.get("recency", 0.20)

    # Entity coverage
    contributions["entity_coverage"] = features.entity_coverage * weights.get(
        "entity_coverage", 0.35
    )

    # Study type
    study_score = STUDY_TYPE_SCORES.get(
        features.study_type_hint.lower(),
        STUDY_TYPE_SCORES["unknown"],
    )
    contributions["study_type"] = study_score * weights.get("study_type", 0.20)

    total = sum(contributions.values())

    return PaperScore(
        paper_id=features.paper_id,
        total_score=total,
        features=features,
        feature_contributions=contributions,
    )


def rank_papers(
    papers: list[PaperFeatures],
    weights: dict[str, float] | None = None,
) -> list[PaperScore]:
    """Rank papers by score.

    Args:
        papers: List of paper features.
        weights: Optional custom weights.

    Returns:
        List of PaperScore sorted by total_score descending.
    """
    scores = [score_paper(p, weights) for p in papers]
    scores.sort(key=lambda x: x.total_score, reverse=True)

    # Add ranks
    for i, score in enumerate(scores):
        score.rank = i + 1

    return scores
