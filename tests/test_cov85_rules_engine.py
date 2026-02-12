from __future__ import annotations

from pathlib import Path

from jarvis_core.rules.engine import RulesEngine


def test_rules_engine_load_context_and_list(tmp_path: Path) -> None:
    workspace_rules = tmp_path / ".agent" / "rules"
    workspace_rules.mkdir(parents=True)
    (workspace_rules / "alpha.md").write_text("workspace rule", encoding="utf-8")

    engine = RulesEngine(workspace_path=tmp_path)
    engine.load_rules()

    listed = engine.list_rules()
    workspace_items = [item for item in listed if item["name"] == "alpha"]
    assert len(workspace_items) == 1
    assert workspace_items[0]["scope"] == "workspace"

    context = engine.get_context_for_llm()
    assert "Rule: alpha" in context
    assert "workspace rule" in context


def test_rules_engine_loaded_flag_prevents_reload(tmp_path: Path) -> None:
    workspace_rules = tmp_path / ".agent" / "rules"
    workspace_rules.mkdir(parents=True)
    first = workspace_rules / "first.md"
    first.write_text("v1", encoding="utf-8")

    engine = RulesEngine(workspace_path=tmp_path)
    engine.load_rules()
    first_count = len(engine.list_rules())

    # because _loaded is True, adding a file does not affect current state
    (workspace_rules / "second.md").write_text("v2", encoding="utf-8")
    assert len(engine.list_rules()) == first_count

    # no workspace path path
    empty_engine = RulesEngine(workspace_path=None)
    no_workspace = empty_engine.list_rules()
    assert all(item["scope"] == "global" for item in no_workspace)
