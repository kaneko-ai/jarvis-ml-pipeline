"""Scoring package."""
from .registry import ScoreRegistry, normalize_score, get_score_info
from .paper_score import score_paper, ScoreResult

__all__ = ["ScoreRegistry", "normalize_score", "get_score_info", "score_paper", "ScoreResult"]
