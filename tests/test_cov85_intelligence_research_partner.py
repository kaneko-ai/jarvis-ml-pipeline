from __future__ import annotations

from types import SimpleNamespace

import pytest

from jarvis_core.intelligence.action_planner import ActionItem, ActionPlan, ActionType, Executor
from jarvis_core.intelligence.goldset_index import GoldsetEntry
from jarvis_core.intelligence.research_partner import (
    ImprovementSuggestion,
    KeyQuestions,
    PastDecisionReference,
    ResearchPartner,
    ResearchPartnerOutput,
    StrategicAssessment,
    StrategicSuggestion,
)


def _make_partner() -> ResearchPartner:
    goldset = SimpleNamespace(search=lambda *_args, **_kwargs: [])
    decisions = SimpleNamespace(list_all=lambda: [])
    outcomes = SimpleNamespace()
    return ResearchPartner(
        goldset_index=goldset, decision_store=decisions, outcome_tracker=outcomes
    )


def test_output_to_markdown_with_all_sections() -> None:
    action_plan = ActionPlan(
        topic="mRNA vaccine",
        read_items=[
            ActionItem(ActionType.READ, "paper-1", "reason-r1", Executor.HUMAN, "human", 5),
            ActionItem(ActionType.READ, "paper-2", "reason-r2", Executor.HUMAN, "human", 4),
        ],
        build_items=[
            ActionItem(ActionType.BUILD, "prototype", "reason-b", Executor.AI, "ai", 4),
        ],
        ignore_items=[
            ActionItem(ActionType.IGNORE, "noise", "reason-i", Executor.AI, "ai", 1),
        ],
    )
    output = ResearchPartnerOutput(
        theme="mRNA vaccine",
        constraints="time budget",
        key_questions=KeyQuestions("q1", "q2", "q3"),
        action_plan=action_plan,
        past_decisions=[
            PastDecisionReference("d1", "reject: x", "failed", "be careful"),
        ],
        strategic=StrategicSuggestion(
            assessment=StrategicAssessment.HOLD,
            reasoning="need caution",
            roi_evaluation="medium",
        ),
        improvements=[
            ImprovementSuggestion("add eval axis", "evaluation_axis"),
            ImprovementSuggestion("improve data", "data"),
        ],
    )

    md = output.to_markdown()
    assert "# Research Partner Report" in md
    assert "**Constraints**: time budget" in md
    assert "## 【Key Questions】" in md
    assert "## 【READ】" in md
    assert "## 【BUILD】" in md
    assert "## 【IGNORE】" in md
    assert "## 【Past Decisions Referenced】" in md
    assert "## 【Strategic Assessment】" in md
    assert "## 【System Improvement Suggestions】" in md


def test_output_to_markdown_minimal() -> None:
    md = ResearchPartnerOutput(theme="tiny").to_markdown()
    assert "**Theme**: tiny" in md
    assert "Constraints" not in md
    assert "Past Decisions" not in md


def test_consult_orchestrates_all_phases(monkeypatch: pytest.MonkeyPatch) -> None:
    partner = _make_partner()
    expected_past = [PastDecisionReference("x", "reject: y", "ok", "z")]
    expected_questions = KeyQuestions("a", "b", "c")
    expected_plan = ActionPlan(topic="t")
    expected_strategic = StrategicSuggestion(StrategicAssessment.GO, "r", "roi")
    expected_improvements = [ImprovementSuggestion("s", "evaluation_axis")]

    calls: list[tuple] = []

    def _ref(theme: str):
        calls.append(("ref", theme))
        return expected_past

    def _q(theme: str, current: str | None):
        calls.append(("q", theme, current))
        return expected_questions

    def _plan(theme: str, constraints: str | None, past: list[PastDecisionReference]):
        calls.append(("plan", theme, constraints, len(past)))
        return expected_plan

    def _strategy(theme: str, past: list[PastDecisionReference]):
        calls.append(("strategy", theme, len(past)))
        return expected_strategic

    def _imp(theme: str, past: list[PastDecisionReference]):
        calls.append(("improve", theme, len(past)))
        return expected_improvements

    monkeypatch.setattr(partner, "_reference_past_decisions", _ref)
    monkeypatch.setattr(partner, "_generate_key_questions", _q)
    monkeypatch.setattr(partner, "_create_action_plan", _plan)
    monkeypatch.setattr(partner, "_assess_strategy", _strategy)
    monkeypatch.setattr(partner, "_suggest_improvements", _imp)

    out = partner.consult("topic-A", constraints="c1", current_situation="s1")
    assert out.theme == "topic-A"
    assert out.key_questions == expected_questions
    assert out.action_plan == expected_plan
    assert out.strategic == expected_strategic
    assert out.improvements == expected_improvements
    assert calls == [
        ("ref", "topic-A"),
        ("q", "topic-A", "s1"),
        ("plan", "topic-A", "c1", 1),
        ("strategy", "topic-A", 1),
        ("improve", "topic-A", 1),
    ]


def test_reference_past_decisions_limits_and_filters() -> None:
    goldset_entries = [
        (
            GoldsetEntry(
                context="ctx1",
                decision="reject",
                scores={},
                reason="too weak",
                outcome="fail",
            ),
            0.9,
        ),
        (
            GoldsetEntry(
                context="ctx2",
                decision="accept",
                scores={},
                reason="strong",
                outcome="success",
            ),
            0.8,
        ),
    ]
    decisions = [
        SimpleNamespace(decision_id="d1", decision="accept", reason="r1", outcome="ok"),
        SimpleNamespace(decision_id="d2", decision="reject", reason="r2", outcome=None),
        SimpleNamespace(decision_id="d3", decision="accept", reason="r3", outcome="great"),
    ]
    partner = ResearchPartner(
        goldset_index=SimpleNamespace(search=lambda *_args, **_kwargs: goldset_entries),
        decision_store=SimpleNamespace(list_all=lambda: decisions),
        outcome_tracker=SimpleNamespace(),
    )

    refs = partner._reference_past_decisions("topic")
    assert len(refs) == 3
    assert refs[0].decision_id.startswith("goldset_")
    assert refs[1].decision_id.startswith("goldset_")
    assert refs[2].decision_id == "d1"
    assert "慎重" in refs[0].implication_for_now
    assert "検討価値" in refs[1].implication_for_now


@pytest.mark.parametrize(
    ("past", "expected"),
    [
        ([PastDecisionReference("1", "reject: a", "x", "y")] * 2, StrategicAssessment.HOLD),
        ([PastDecisionReference("1", "reject: a", "x", "y")], StrategicAssessment.HOLD),
        ([PastDecisionReference("1", "accept: a", "x", "y")], StrategicAssessment.GO),
    ],
)
def test_assess_strategy_branches(
    past: list[PastDecisionReference], expected: StrategicAssessment
) -> None:
    partner = _make_partner()
    strategic = partner._assess_strategy("topic", past)
    assert strategic.assessment == expected
    assert strategic.roi_evaluation


def test_generate_key_questions_and_action_plan() -> None:
    partner = _make_partner()
    questions = partner._generate_key_questions("gene editing", None)
    assert "gene editing" in questions.unverified
    assert questions.implicit_assumption
    assert questions.decision_point

    plan = partner._create_action_plan(
        "gene editing",
        constraints="limited budget",
        past_decisions=[PastDecisionReference("x", "reject: old", "n/a", "skip")],
    )
    assert len(plan.read_items) == 2
    assert len(plan.build_items) == 1
    assert len(plan.ignore_items) == 2
    assert plan.read_items[0].action_type == ActionType.READ
    assert plan.build_items[0].action_type == ActionType.BUILD
    assert plan.ignore_items[0].action_type == ActionType.IGNORE


def test_suggest_improvements_branching() -> None:
    partner = _make_partner()
    short_history = partner._suggest_improvements("topic", [])
    assert len(short_history) == 2
    assert short_history[0].category == "data"
    assert short_history[1].category == "evaluation_axis"

    long_history = partner._suggest_improvements(
        "topic",
        [
            PastDecisionReference("1", "accept", "ok", "x"),
            PastDecisionReference("2", "accept", "ok", "x"),
        ],
    )
    assert len(long_history) == 1
    assert long_history[0].category == "evaluation_axis"
