"""Repair Planner.

Per RP-186, plans repair actions based on failure signals.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from ..failure_signal import FailureSignal, FailureCode
from .catalog import get_action


# Default repair rules (RP-199: can be overridden by JSON)
DEFAULT_RULES = {
    FailureCode.FETCH_PDF_FAILED.value: ["SWITCH_FETCH_ADAPTER", "INCREASE_TOP_K"],
    FailureCode.EXTRACT_PDF_FAILED.value: ["SWITCH_FETCH_ADAPTER", "INCREASE_TOP_K"],
    FailureCode.CITATION_GATE_FAILED.value: ["INCREASE_TOP_K", "TIGHTEN_MMR", "CITATION_FIRST_PROMPT"],
    FailureCode.LOW_CLAIM_PRECISION.value: ["TIGHTEN_MMR", "INCREASE_TOP_K"],
    FailureCode.BUDGET_EXCEEDED.value: ["BUDGET_REBALANCE"],
    FailureCode.MODEL_ERROR.value: ["MODEL_ROUTER_SAFE_SWITCH"],
    FailureCode.JUDGE_TIMEOUT.value: ["MODEL_ROUTER_SAFE_SWITCH"],
    FailureCode.ENTITY_MISS.value: ["INCREASE_TOP_K"],
}


class RepairPlanner:
    """Plans repair actions from failure signals.

    Per RP-186, the planner:
    - Uses deterministic, fixed-priority rules
    - Guards against applying same action consecutively
    - Supports JSON-driven rule configuration (RP-199)
    """

    def __init__(self, rules_path: Optional[str] = None):
        self._rules = dict(DEFAULT_RULES)

        # Load custom rules if provided (RP-199)
        if rules_path:
            self._load_rules(rules_path)

    def _load_rules(self, rules_path: str) -> None:
        """Load rules from JSON file."""
        path = Path(rules_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                custom_rules = json.load(f)
                for code, actions in custom_rules.items():
                    self._rules[code] = actions

    def plan(
        self,
        signals: List[FailureSignal],
        state: Dict[str, Any],
        run_config: Dict[str, Any],
    ) -> List[str]:
        """Plan repair actions for given signals.

        Args:
            signals: List of failure signals.
            state: Current state including action history.
            run_config: Current run configuration.

        Returns:
            Ordered list of action IDs to apply.
        """
        if not signals:
            return []

        # Get action history to avoid repetition
        history: List[str] = state.get("action_history", [])
        last_action = history[-1] if history else None
        recent_actions: Set[str] = set(history[-3:]) if history else set()

        # Allowed actions from policy
        allowed = set(run_config.get("repair_policy", {}).get("allowed_actions", []))
        if not allowed:
            # Default all if not specified
            allowed = set(self._rules.get(signals[0].code.value, []))

        planned = []

        # Process signals in order (priority by signal order)
        for signal in signals:
            code = signal.code.value if hasattr(signal.code, 'value') else signal.code
            actions = self._rules.get(code, [])

            for action_id in actions:
                # Skip if not allowed
                if allowed and action_id not in allowed:
                    continue

                # Skip if same as last action (consecutive guard)
                if action_id == last_action:
                    continue

                # Skip if already planned
                if action_id in planned:
                    continue

                # Skip if recently applied (avoid loops)
                if len(recent_actions) >= 3 and action_id in recent_actions:
                    continue

                # Verify action exists
                if get_action(action_id):
                    planned.append(action_id)
                    break  # One action per signal

        return planned

    def get_rules(self) -> Dict[str, List[str]]:
        """Get current rules."""
        return dict(self._rules)


# Global planner
_planner: Optional[RepairPlanner] = None


def get_planner(rules_path: Optional[str] = None) -> RepairPlanner:
    """Get global planner."""
    global _planner
    if _planner is None:
        _planner = RepairPlanner(rules_path)
    return _planner


def plan_repair(
    signals: List[FailureSignal],
    state: Dict[str, Any],
    run_config: Dict[str, Any],
) -> List[str]:
    """Plan repair using global planner."""
    return get_planner().plan(signals, state, run_config)
