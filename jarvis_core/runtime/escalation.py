"""Escalation Logic (Phase 2 Step 5).

Monitors eval_summary and triggers additional inference when quality is low.
Based on inference_policy.yaml escalation rules.
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class InferenceEscalator:
    """Controls test-time scaling based on quality metrics."""

    def __init__(self, policy_path: Path = Path("policies/inference_policy.yaml")):
        self.policy = self._load_policy(policy_path)
        self.escalation_rules = self.policy.get("escalation_rules", [])

    def _load_policy(self, path: Path) -> dict:
        """Load inference policy from YAML."""
        if not path.exists():
            logger.warning(f"Policy not found: {path}, using defaults")
            return {"escalation_rules": []}

        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f).get("policy", {})

    def should_escalate(self, eval_summary: dict) -> list[dict]:
        """Check if escalation is needed based on eval_summary.

        Returns:
            List of escalation actions to take
        """
        actions = []

        for rule in self.escalation_rules:
            trigger = rule.get("trigger", {})
            metric_name = trigger.get("metric")
            condition = trigger.get("condition")
            threshold = trigger.get("threshold")

            # Get metric value from eval_summary
            metric_value = self._get_metric_value(eval_summary, metric_name)

            if metric_value is None:
                continue

            # Check condition
            triggered = False
            if condition == "<" and metric_value < threshold:
                triggered = True
            elif condition == ">" and metric_value > threshold:
                triggered = True
            elif condition == "==" and metric_value == threshold:
                triggered = True

            if triggered:
                action = rule.get("action", {})
                logger.info(
                    f"Escalation triggered: {metric_name} {condition} {threshold} (value={metric_value})"
                )
                actions.append(action)

        return actions

    def _get_metric_value(self, eval_summary: dict, metric_name: str):
        """Extract metric value from eval_summary."""
        metrics = eval_summary.get("metrics", {})

        # Common metrics
        if metric_name == "provenance_rate":
            return metrics.get("provenance_rate") or metrics.get("evidence_coverage", 0)
        elif metric_name == "contradiction_flag_count":
            return metrics.get("contradiction_count", 0)
        elif metric_name == "top_k_tie_margin":
            # This would come from ranking scores
            return metrics.get("top_k_tie_margin", 1.0)

        return metrics.get(metric_name)

    def execute_actions(self, actions: list[dict], context, artifacts) -> dict:
        """Execute escalation actions.

        In production, this would trigger actual additional stages.
        For Phase 2, we log and return metadata.
        """
        results = {
            "escalation_triggered": len(actions) > 0,
            "actions_taken": [],
            "additional_cost": 0,
        }

        for action in actions:
            action_type = action.get("type")
            params = action.get("params", {})

            logger.info(f"Executing escalation: {action_type} with params {params}")

            # Mock execution (in production, trigger actual stages)
            if action_type == "evidence_search_expand":
                # Would trigger additional retrieval
                results["actions_taken"].append(
                    {
                        "type": action_type,
                        "status": "simulated",
                        "additional_papers": params.get("max_additional_papers", 5),
                    }
                )
                results["additional_cost"] += 1000  # Mock token cost

            elif action_type == "refutation_search":
                results["actions_taken"].append({"type": action_type, "status": "simulated"})
                results["additional_cost"] += 500

            elif action_type == "feature_extraction_expand":
                results["actions_taken"].append(
                    {
                        "type": action_type,
                        "status": "simulated",
                        "additional_features": params.get("additional_features", []),
                    }
                )
                results["additional_cost"] += 200

        return results


def get_escalator(policy_path: Path = Path("policies/inference_policy.yaml")) -> InferenceEscalator:
    """Get escalator instance."""
    return InferenceEscalator(policy_path)
