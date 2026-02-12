from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.eval.regression import (
    PromptRegressionChecker,
    check_regression,
    create_baseline_scores,
)


def test_prompt_regression_set_and_check_degradation_and_improvement(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    checker = PromptRegressionChecker(baseline_path=baseline_path, tolerance=0.0)

    checker.set_baseline(
        prompt_id="p1",
        version="1.0",
        prompt_hash="h1",
        metrics={"evidence_coverage": 1.0, "locator_rate": 1.0},
    )

    degraded = checker.check("p1", "1.0", {"evidence_coverage": 0.8, "locator_rate": 1.2})
    assert degraded.passed is False
    assert any(m["metric"] == "evidence_coverage" for m in degraded.degraded_metrics)
    assert any(m["metric"] == "locator_rate" for m in degraded.improved_metrics)


def test_prompt_regression_no_baseline_and_check_all(tmp_path: Path) -> None:
    checker = PromptRegressionChecker(baseline_path=tmp_path / "none.json")

    result = checker.check("unknown", "9", {"x": 1.0})
    assert result.passed is True
    assert result.baseline is None

    checker.set_baseline("p2", "1", "h", {"evidence_coverage": 0.9})
    all_results = checker.check_all({"p2:1": {"evidence_coverage": 0.9}, "p3": {"a": 1}})
    assert len(all_results) == 2


def test_create_baseline_scores_and_load_failure_and_helper(tmp_path: Path) -> None:
    out = tmp_path / "evals" / "baseline_scores.json"
    create_baseline_scores(out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "paper_survey_retrieve:1.0" in data

    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{bad", encoding="utf-8")
    checker = PromptRegressionChecker(baseline_path=bad_path)
    assert checker.check("x", "1", {"evidence_coverage": 1.0}).passed is True

    helper_result = check_regression("random-prompt", "1", {"evidence_coverage": 1.0})
    assert helper_result.prompt_id == "random-prompt"
