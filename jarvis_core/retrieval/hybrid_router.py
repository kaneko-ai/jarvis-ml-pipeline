"""Hybrid Router.

Per V4.2 Sprint 3, this routes queries to BM25/Dense/Both based on query characteristics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional


class RouteDecision(Enum):
    """Routing decisions."""

    BM25_ONLY = "bm25_only"       # Keyword-focused query
    DENSE_ONLY = "dense_only"     # Semantic query
    HYBRID = "hybrid"             # Both methods


@dataclass
class RoutingResult:
    """Result of routing decision."""

    decision: RouteDecision
    confidence: float
    reasons: List[str]
    query_features: Dict[str, Any]


class HybridRouter:
    """Routes queries to appropriate retrieval method."""

    def __init__(
        self,
        bm25_keywords_threshold: int = 5,
        dense_cost_multiplier: float = 2.0,
    ):
        self.bm25_keywords_threshold = bm25_keywords_threshold
        self.dense_cost_multiplier = dense_cost_multiplier

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query characteristics."""
        words = query.lower().split()

        # Check for technical terms
        technical_patterns = [
            "cd73", "pd-1", "ctla-4", "mrna", "dna",
            "gene", "protein", "pathway", "mechanism",
        ]
        has_technical = any(p in query.lower() for p in technical_patterns)

        # Check for conceptual queries
        conceptual_patterns = [
            "how", "why", "explain", "relationship",
            "compare", "difference", "similar",
        ]
        is_conceptual = any(p in query.lower() for p in conceptual_patterns)

        # Check specificity
        has_numbers = any(c.isdigit() for c in query)
        word_count = len(words)

        return {
            "word_count": word_count,
            "has_technical": has_technical,
            "is_conceptual": is_conceptual,
            "has_numbers": has_numbers,
            "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
        }

    def route(
        self,
        query: str,
        budget_remaining: Optional[float] = None,
    ) -> RoutingResult:
        """Determine routing for query.

        Args:
            query: Search query.
            budget_remaining: Optional remaining budget (0-1).

        Returns:
            RoutingResult with decision.
        """
        features = self.analyze_query(query)
        reasons = []

        # Budget constraint - prefer cheaper BM25
        if budget_remaining is not None and budget_remaining < 0.3:
            return RoutingResult(
                decision=RouteDecision.BM25_ONLY,
                confidence=0.9,
                reasons=["Budget constraint - using BM25 only"],
                query_features=features,
            )

        # Technical keyword queries -> BM25 is effective
        if features["has_technical"] and features["word_count"] <= 3:
            reasons.append("Short technical query")
            return RoutingResult(
                decision=RouteDecision.BM25_ONLY,
                confidence=0.8,
                reasons=reasons,
                query_features=features,
            )

        # Conceptual queries -> Dense is better
        if features["is_conceptual"]:
            reasons.append("Conceptual/semantic query")
            return RoutingResult(
                decision=RouteDecision.DENSE_ONLY,
                confidence=0.7,
                reasons=reasons,
                query_features=features,
            )

        # Long queries or mixed -> Hybrid
        if features["word_count"] > self.bm25_keywords_threshold:
            reasons.append("Long query benefits from hybrid")
            return RoutingResult(
                decision=RouteDecision.HYBRID,
                confidence=0.6,
                reasons=reasons,
                query_features=features,
            )

        # Default to hybrid for best coverage
        return RoutingResult(
            decision=RouteDecision.HYBRID,
            confidence=0.5,
            reasons=["Default hybrid for coverage"],
            query_features=features,
        )


def create_default_router() -> HybridRouter:
    """Create router with default settings."""
    return HybridRouter()
