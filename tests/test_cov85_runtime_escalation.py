from __future__ import annotations

from pathlib import Path

from jarvis_core.runtime.escalation import InferenceEscalator, get_escalator


def test_load_policy_missing_file_uses_default(tmp_path: Path) -> None:
    escalator = InferenceEscalator(policy_path=tmp_path / "missing.yaml")
    assert escalator.escalation_rules == []
    assert escalator.should_escalate({"metrics": {"provenance_rate": 0.1}}) == []
    assert escalator.execute_actions([], context={}, artifacts={}) == {
        "escalation_triggered": False,
        "actions_taken": [],
        "additional_cost": 0,
    }


def test_should_escalate_multiple_conditions_and_metric_fallback(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
policy:
  escalation_rules:
    - trigger:
        metric: provenance_rate
        condition: "<"
        threshold: 0.9
      action:
        type: evidence_search_expand
        params:
          max_additional_papers: 7
    - trigger:
        metric: contradiction_flag_count
        condition: ">"
        threshold: 2
      action:
        type: refutation_search
    - trigger:
        metric: top_k_tie_margin
        condition: "=="
        threshold: 0.5
      action:
        type: feature_extraction_expand
        params:
          additional_features: ["x"]
""",
        encoding="utf-8",
    )

    escalator = InferenceEscalator(policy_path=policy_path)
    actions = escalator.should_escalate(
        {
            "metrics": {
                "evidence_coverage": 0.8,
                "contradiction_count": 3,
                "top_k_tie_margin": 0.5,
            }
        }
    )
    assert len(actions) == 3

    results = escalator.execute_actions(actions, context={}, artifacts={})
    assert results["escalation_triggered"] is True
    assert len(results["actions_taken"]) == 3
    assert results["additional_cost"] == 1700


def test_execute_actions_unknown_type_and_get_escalator(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy2.yaml"
    policy_path.write_text("policy: {escalation_rules: []}", encoding="utf-8")

    escalator = get_escalator(policy_path)
    result = escalator.execute_actions([{"type": "unknown", "params": {}}], {}, {})
    assert result["escalation_triggered"] is True
    assert result["actions_taken"] == []
    assert result["additional_cost"] == 0
