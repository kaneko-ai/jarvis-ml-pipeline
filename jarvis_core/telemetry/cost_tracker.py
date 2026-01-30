"""Telemetry cost tracker for stage-level reporting."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StageCost:
    """Cost metrics for a single stage."""

    tokens: int
    time_ms: int
    api_calls: int


@dataclass
class CostTracker:
    """Track token/time/API usage by stage."""

    _stages: dict[str, StageCost] = field(default_factory=dict)

    def track_stage(self, stage_name: str, tokens: int, time_ms: int, api_calls: int) -> None:
        """Track cost for a stage.

        Args:
            stage_name: Stage identifier.
            tokens: Token count for the stage.
            time_ms: Stage duration in milliseconds.
            api_calls: API calls for the stage.
        """
        self._stages[stage_name] = StageCost(tokens=tokens, time_ms=time_ms, api_calls=api_calls)

    def get_report(self) -> dict[str, dict[str, int] | dict[str, dict[str, int]]]:
        """Return a cost report with totals and per-stage breakdown."""
        totals = {
            "tokens": sum(stage.tokens for stage in self._stages.values()),
            "time_ms": sum(stage.time_ms for stage in self._stages.values()),
            "api_calls": sum(stage.api_calls for stage in self._stages.values()),
        }
        by_stage = {
            stage_name: {
                "tokens": stage.tokens,
                "time_ms": stage.time_ms,
                "api_calls": stage.api_calls,
            }
            for stage_name, stage in self._stages.items()
        }
        return {"totals": totals, "by_stage": by_stage}