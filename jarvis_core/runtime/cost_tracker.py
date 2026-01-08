"""Cost Tracking for JARVIS Runs (Phase 2-ΩΩ).

Tracks and reports inference costs, tokens, API calls, and execution time
for each stage in a pipeline run.
"""
import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CostTracker:
    """Track costs for a pipeline run."""

    def __init__(self):
        self.stages = []
        self.start_time = time.time()

    def record_stage(
        self,
        stage_name: str,
        duration_ms: int,
        api_calls: int = 0,
        tokens: dict[str, int] | None = None,
        retries: int = 0,
        cache_hits: int = 0
    ):
        """Record cost information for a stage.
        
        Args:
            stage_name: Name of the stage
            duration_ms: Duration in milliseconds
            api_calls: Number of API calls made
            tokens: Dict with 'prompt' and 'completion' token counts
            retries: Number of retry attempts
            cache_hits: Number of cache hits
        """
        stage_cost = {
            "stage_name": stage_name,
            "duration_ms": duration_ms,
            "api_calls": api_calls,
            "prompt_tokens": tokens.get("prompt") if tokens else None,
            "completion_tokens": tokens.get("completion") if tokens else None,
            "retries": retries,
            "cache_hits": cache_hits,
        }

        self.stages.append(stage_cost)
        logger.info(f"Recorded cost for {stage_name}: {duration_ms}ms, {api_calls} API calls")

    def get_total_cost(self) -> dict[str, Any]:
        """Calculate total costs across all stages.
        
        Returns:
            Dict with aggregated costs
        """
        total_duration = sum(s["duration_ms"] for s in self.stages)
        total_api_calls = sum(s["api_calls"] for s in self.stages)
        total_prompt_tokens = sum(
            s["prompt_tokens"] for s in self.stages if s["prompt_tokens"] is not None
        )
        total_completion_tokens = sum(
            s["completion_tokens"] for s in self.stages if s["completion_tokens"] is not None
        )
        total_retries = sum(s["retries"] for s in self.stages)

        return {
            "total_duration_ms": total_duration,
            "total_api_calls": total_api_calls,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "total_retries": total_retries,
            "stage_count": len(self.stages),
        }

    def export(self, run_dir: Path):
        """Export cost report to JSON.
        
        Args:
            run_dir: Path to run directory
        """
        cost_report = {
            "stages": self.stages,
            "totals": self.get_total_cost(),
            "elapsed_time_s": time.time() - self.start_time,
        }

        output_path = run_dir / "cost_report.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cost_report, f, indent=2, ensure_ascii=False)

        logger.info(f"Cost report exported to {output_path}")

        return cost_report


def check_budget_exceeded(
    cost_report: dict[str, Any],
    budget_tokens: int | None = None
) -> bool:
    """Check if budget was exceeded.
    
    Args:
        cost_report: Cost report dict
        budget_tokens: Maximum allowed tokens
        
    Returns:
        True if budget exceeded
    """
    if budget_tokens is None:
        return False

    totals = cost_report.get("totals", {})
    total_tokens = totals.get("total_tokens", 0)

    return total_tokens > budget_tokens
