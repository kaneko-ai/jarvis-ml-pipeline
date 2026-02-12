from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from jarvis_core.autonomous_loop import get_intervention_summary, run_autonomous_research_loop


@pytest.fixture
def _patch_loop_dependencies(monkeypatch: pytest.MonkeyPatch):
    def _apply(gap_scores, hypotheses, feasibility_score):
        gap_iter = iter(gap_scores)

        def _score_research_gaps(vectors, concept):  # noqa: ANN001
            return [{"concept": concept, "gap_score": next(gap_iter)}]

        def _generate_hypotheses(vectors, concepts):  # noqa: ANN001
            return [{"hypothesis": h, "based_on": ["m1"]} for h in hypotheses]

        def _score_feasibility(hypothesis, vectors):  # noqa: ANN001
            return {"overall": feasibility_score, "hypothesis": hypothesis}

        mod_gap = SimpleNamespace(score_research_gaps=_score_research_gaps)
        mod_hyp = SimpleNamespace(generate_hypotheses=_generate_hypotheses)
        mod_fea = SimpleNamespace(score_feasibility=_score_feasibility)

        monkeypatch.setitem(sys.modules, "jarvis_core.gap_analysis", mod_gap)
        monkeypatch.setitem(sys.modules, "jarvis_core.hypothesis", mod_hyp)
        monkeypatch.setitem(sys.modules, "jarvis_core.feasibility", mod_fea)

    return _apply


def test_run_autonomous_research_loop_no_input() -> None:
    result = run_autonomous_research_loop([], [], max_iterations=2)
    assert result["status"] == "no_input"
    assert result["iterations"] == []


def test_run_autonomous_research_loop_convergence_and_summary(
    _patch_loop_dependencies,
) -> None:
    _patch_loop_dependencies(gap_scores=[0.0, 0.0], hypotheses=["h1", "h2"], feasibility_score=0.8)

    result = run_autonomous_research_loop([{"v": 1}], ["c1", "c2"], max_iterations=3)
    assert result["status"] == "completed"
    assert result["convergence"] is True
    assert len(result["iterations"]) == 1
    assert result["total_hypotheses"] == 2
    assert result["total_experiments"] == 2

    summary = get_intervention_summary(result)
    assert summary.strip() != ""
    assert "[Iter" not in summary


def test_run_autonomous_research_loop_multiple_iterations_and_interventions(
    _patch_loop_dependencies,
) -> None:
    # 2 concepts x 2 iterations = 4 gap scores consumed
    _patch_loop_dependencies(
        gap_scores=[0.9, 0.8, 0.7, 0.6],
        hypotheses=["h1", "h2", "h3", "h4", "h5", "h6"],
        feasibility_score=0.2,
    )

    result = run_autonomous_research_loop([{"v": 1}], ["c1", "c2"], max_iterations=2)
    assert result["convergence"] is False
    assert len(result["iterations"]) == 2
    assert result["iterations"][0]["human_intervention_points"]
    assert result["final_recommendations"]

    text = get_intervention_summary(result)
    assert "[Iter 1]" in text


def test_get_intervention_summary_empty() -> None:
    summary = get_intervention_summary({"iterations": []})
    assert summary.strip() != ""
    assert "[Iter" not in summary
