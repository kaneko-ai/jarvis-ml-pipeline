"""Repair Loop.

Per RP-187, implements the retry-until-success loop.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .failure_signal import FailureSignal, extract_failure_signals
from .remediation import get_action
from .remediation.planner import plan_repair
from .repair_policy import RepairPolicy


class StopReason(Enum):
    """Reasons for stopping the repair loop."""

    SUCCESS = "success"
    MAX_ATTEMPTS = "max_attempts"
    MAX_WALL_TIME = "max_wall_time"
    MAX_TOOL_CALLS = "max_tool_calls"
    NO_IMPROVEMENT = "no_improvement"
    SAME_FAILURE_REPEATED = "same_failure_repeated"
    NO_ACTIONS_AVAILABLE = "no_actions_available"


@dataclass
class RepairLoopResult:
    """Result of repair loop execution."""

    final_result: Any
    stop_reason: StopReason
    attempts: int
    action_history: list[str]
    failure_signals_history: list[list[FailureSignal]]
    total_time_seconds: float


class RepairLoop:
    """Executes repair loop until success or stop condition.

    Per RP-187:
    - Attempts 1..max_attempts
    - Each attempt: run → result → signals → plan → apply → next
    - Stops on: max_attempts, wall_time, tool_calls, no improvement, repeated failure
    """

    def __init__(
        self,
        policy: RepairPolicy,
        run_fn: Callable[[dict[str, Any]], Any],
        quality_fn: Callable[[Any], bool],
    ):
        """Initialize repair loop.

        Args:
            policy: RepairPolicy with limits and allowed actions.
            run_fn: Function to execute a run with given config.
            quality_fn: Function to check if result meets quality bar.
        """
        self.policy = policy
        self.run_fn = run_fn
        self.quality_fn = quality_fn

    def run(self, initial_config: dict[str, Any]) -> RepairLoopResult:
        """Execute the repair loop.

        Args:
            initial_config: Initial run configuration.

        Returns:
            RepairLoopResult with final outcome and metadata.
        """
        start_time = time.time()
        config = dict(initial_config)
        config["repair_policy"] = self.policy.to_dict()

        action_history: list[str] = []
        signals_history: list[list[FailureSignal]] = []
        tool_calls = 0
        consecutive_no_improvement = 0
        last_failure_codes: set | None = None

        for attempt in range(1, self.policy.max_attempts + 1):
            # Check wall time
            elapsed = time.time() - start_time
            if elapsed >= self.policy.max_wall_time_sec:
                return RepairLoopResult(
                    final_result=None,
                    stop_reason=StopReason.MAX_WALL_TIME,
                    attempts=attempt,
                    action_history=action_history,
                    failure_signals_history=signals_history,
                    total_time_seconds=elapsed,
                )

            # Check tool calls
            if tool_calls >= self.policy.max_tool_calls:
                return RepairLoopResult(
                    final_result=None,
                    stop_reason=StopReason.MAX_TOOL_CALLS,
                    attempts=attempt,
                    action_history=action_history,
                    failure_signals_history=signals_history,
                    total_time_seconds=time.time() - start_time,
                )

            # Execute run
            tool_calls += 1
            result = self.run_fn(config)

            # Check quality
            if self.quality_fn(result):
                return RepairLoopResult(
                    final_result=result,
                    stop_reason=StopReason.SUCCESS,
                    attempts=attempt,
                    action_history=action_history,
                    failure_signals_history=signals_history,
                    total_time_seconds=time.time() - start_time,
                )

            # Extract failure signals
            signals = extract_failure_signals(result)
            signals_history.append(signals)

            # Check for repeated failure (RP-192 kill switch)
            current_codes = {s.code for s in signals}
            if current_codes == last_failure_codes:
                consecutive_no_improvement += 1
                if self.policy.should_stop_on_no_improvement(consecutive_no_improvement):
                    return RepairLoopResult(
                        final_result=result,
                        stop_reason=StopReason.NO_IMPROVEMENT,
                        attempts=attempt,
                        action_history=action_history,
                        failure_signals_history=signals_history,
                        total_time_seconds=time.time() - start_time,
                    )
            else:
                consecutive_no_improvement = 0
                last_failure_codes = current_codes

            # Plan actions
            state = {"action_history": action_history}
            planned_actions = plan_repair(signals, state, config)

            if not planned_actions:
                return RepairLoopResult(
                    final_result=result,
                    stop_reason=StopReason.NO_ACTIONS_AVAILABLE,
                    attempts=attempt,
                    action_history=action_history,
                    failure_signals_history=signals_history,
                    total_time_seconds=time.time() - start_time,
                )

            # Apply actions
            for action_id in planned_actions:
                if not self.policy.is_action_allowed(action_id):
                    continue

                action = get_action(action_id)
                if action:
                    action_result = action.apply(config, state)
                    if action_result.success:
                        config.update(action_result.config_changes)
                        action_history.append(action_id)
                        tool_calls += 1

        # Max attempts reached
        return RepairLoopResult(
            final_result=None,
            stop_reason=StopReason.MAX_ATTEMPTS,
            attempts=self.policy.max_attempts,
            action_history=action_history,
            failure_signals_history=signals_history,
            total_time_seconds=time.time() - start_time,
        )