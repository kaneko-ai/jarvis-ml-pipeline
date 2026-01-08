"""Quality Estimator.

Per V4.2 Sprint 3, this estimates quality gain from processing choices.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QualityEstimator:
    """Estimates quality improvements from processing choices."""

    # Base quality by method
    base_quality: dict[str, float] = field(
        default_factory=lambda: {
            "bm25_only": 0.6,
            "dense_only": 0.7,
            "hybrid": 0.85,
            "hybrid_rerank": 0.95,
        }
    )

    # Quality boost factors
    evidence_boost: float = 0.1  # Per evidence found
    rerank_boost: float = 0.15  # Reranking improvement
    deep_analysis_boost: float = 0.1  # Deep vs quick

    def estimate_retrieval_quality(
        self,
        method: str,
        candidate_count: int,
        reranked: bool = False,
    ) -> float:
        """Estimate retrieval quality."""
        base = self.base_quality.get(method, 0.5)

        # More candidates → higher recall potential
        count_factor = min(candidate_count / 100, 1.0) * 0.1

        # Reranking boost
        rerank_factor = self.rerank_boost if reranked else 0

        return min(base + count_factor + rerank_factor, 1.0)

    def estimate_answer_quality(
        self,
        evidence_count: int,
        retrieval_quality: float,
        analysis_depth: str = "quick",
    ) -> float:
        """Estimate final answer quality."""
        # Evidence contribution (diminishing returns)
        evidence_factor = min(evidence_count * 0.05, 0.3)

        # Depth contribution
        depth_factor = self.deep_analysis_boost if analysis_depth == "deep" else 0

        # Combined quality
        quality = retrieval_quality * 0.6 + evidence_factor + depth_factor

        return min(quality, 1.0)


def estimate_quality(
    method: str = "hybrid",
    candidate_count: int = 50,
    evidence_count: int = 5,
    reranked: bool = False,
    analysis_depth: str = "quick",
    estimator: QualityEstimator = None,
) -> float:
    """Estimate overall quality.

    Args:
        method: Retrieval method.
        candidate_count: Number of candidates.
        evidence_count: Number of evidence pieces.
        reranked: Whether reranking was used.
        analysis_depth: "quick" or "deep".
        estimator: Quality estimator.

    Returns:
        Estimated quality (0-1).
    """
    estimator = estimator or QualityEstimator()

    retrieval_q = estimator.estimate_retrieval_quality(method, candidate_count, reranked)

    answer_q = estimator.estimate_answer_quality(evidence_count, retrieval_q, analysis_depth)

    return answer_q
