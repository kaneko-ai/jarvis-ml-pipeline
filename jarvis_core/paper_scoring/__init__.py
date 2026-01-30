"""JARVIS Paper Scoring Module.

Calculates overall quality/reliability scores for research papers.
Per JARVIS_COMPLETION_PLAN_v3 Sprint 19-20
"""

from jarvis_core.paper_scoring.scorer import (
    PaperScore,
    PaperScorer,
    ScoringWeights,
    calculate_paper_score,
)

__all__ = [
    "PaperScore",
    "PaperScorer",
    "ScoringWeights",
    "calculate_paper_score",
]
