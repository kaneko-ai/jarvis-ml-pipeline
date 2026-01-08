"""Scoring package."""

from .paper_score import ScoreResult, score_paper
from .registry import ScoreRegistry, get_score_info, normalize_score

__all__ = ["ScoreRegistry", "normalize_score", "get_score_info", "score_paper", "ScoreResult"]
