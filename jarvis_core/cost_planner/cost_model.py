"""Cost Model.

Per V4.2 Sprint 3, this estimates execution cost from span measurements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class CostModel:
    """Model for estimating execution costs."""

    # Token costs (per 1K tokens)
    input_token_cost: float = 0.001
    output_token_cost: float = 0.003

    # Time costs (per second)
    compute_cost_per_second: float = 0.0001

    # Stage cost multipliers
    stage_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "extraction": 1.0,
        "indexing": 0.5,
        "retrieval:stage1": 0.1,
        "retrieval:stage2_rerank": 2.0,
        "generation": 3.0,
    })

    def estimate_token_cost(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost from token counts."""
        input_cost = (input_tokens / 1000) * self.input_token_cost
        output_cost = (output_tokens / 1000) * self.output_token_cost
        return input_cost + output_cost

    def estimate_stage_cost(
        self,
        stage: str,
        duration_ms: float,
        item_count: int = 0,
    ) -> float:
        """Estimate cost for a processing stage."""
        base_cost = (duration_ms / 1000) * self.compute_cost_per_second
        multiplier = self.stage_multipliers.get(stage, 1.0)
        return base_cost * multiplier

    def estimate_from_spans(
        self,
        span_stats: Dict[str, dict],
    ) -> Dict[str, float]:
        """Estimate costs from span statistics."""
        costs = {}
        total = 0.0

        for stage, stats in span_stats.items():
            duration = stats.get("total_ms", 0)
            cost = self.estimate_stage_cost(stage, duration)
            costs[stage] = cost
            total += cost

        costs["total"] = total
        return costs


def estimate_cost(
    span_stats: Dict[str, dict],
    tokens_used: int = 0,
    model: CostModel = None,
) -> float:
    """Estimate total execution cost.

    Args:
        span_stats: Span statistics.
        tokens_used: Total tokens used.
        model: Cost model.

    Returns:
        Estimated cost.
    """
    model = model or CostModel()
    stage_costs = model.estimate_from_spans(span_stats)
    token_cost = model.estimate_token_cost(tokens_used, tokens_used // 4)
    return stage_costs["total"] + token_cost
