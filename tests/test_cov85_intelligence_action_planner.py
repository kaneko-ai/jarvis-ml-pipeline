from __future__ import annotations

from jarvis_core.intelligence.action_planner import ActionPlan, ActionPlanner, ActionType, Executor


def test_action_planner_classification_and_sorting() -> None:
    planner = ActionPlanner()
    plan = planner.plan(
        topic="t",
        candidates=[
            {"title": "LowRel", "type": "paper", "relevance": 1, "evidence": 5},
            {"title": "StrongPaper", "type": "paper", "relevance": 5, "evidence": 4},
            {"title": "Impl", "type": "code", "relevance": 4, "evidence": 1},
            {"title": "Other", "type": "note", "relevance": 3, "evidence": 1},
        ],
    )

    assert [i.target for i in plan.read_items] == ["StrongPaper", "Other"]
    assert [i.target for i in plan.build_items] == ["Impl"]
    assert [i.target for i in plan.ignore_items] == ["LowRel"]

    assert plan.read_items[0].action_type == ActionType.READ
    assert plan.read_items[0].executor == Executor.HUMAN
    assert plan.build_items[0].executor == Executor.AI


def test_action_item_to_dict_and_markdown_output() -> None:
    planner = ActionPlanner()
    quick = planner.quick_plan(
        topic="X",
        top_papers=["P1"],
        implementation_ideas=["I1"],
        low_priority=["L1"],
    )

    md = quick.to_markdown()
    assert "Action Plan: X" in md
    assert "READ" in md and "BUILD" in md and "IGNORE" in md

    first = quick.read_items[0].to_dict()
    assert first["action"] == "read"
    assert first["executor"] == "human"


def test_empty_action_plan_markdown() -> None:
    empty = ActionPlan(topic="Empty")
    md = empty.to_markdown()
    assert "Action Plan: Empty" in md
