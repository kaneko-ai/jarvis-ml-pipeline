from __future__ import annotations

from pathlib import Path

import pytest

from jarvis_core.workflows.engine import WorkflowsEngine


def test_workflows_engine_discover_list_get_and_execute(tmp_path: Path) -> None:
    wf_dir = tmp_path / ".agent" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "w1.md").write_text(
        "---\nname: custom\ndescription: desc\ncommand: run\n---\n- step1\n- step2\n",
        encoding="utf-8",
    )

    engine = WorkflowsEngine(workspace_path=tmp_path)
    listed = engine.list_workflows()
    assert len(listed) >= 1
    assert any(item["name"] == "custom" for item in listed)

    wf = engine.get_workflow("custom")
    assert wf is not None
    text = engine.execute("custom", {"x": 1})
    assert "Workflow Execution" in text
    assert "custom" in text
    assert '"x": 1' in text


def test_workflows_engine_execute_missing_and_parse_without_frontmatter(tmp_path: Path) -> None:
    wf_file = tmp_path / ".agent" / "workflows" / "plain.md"
    wf_file.parent.mkdir(parents=True)
    wf_file.write_text("just body", encoding="utf-8")

    engine = WorkflowsEngine(workspace_path=tmp_path)
    wf = engine.get_workflow("plain")
    assert wf is not None
    assert wf.metadata.name == "plain"
    assert wf.content == "just body"

    with pytest.raises(ValueError):
        engine.execute("missing", {})


def test_workflows_parse_frontmatter_static_method(tmp_path: Path) -> None:
    path = tmp_path / "wf.md"
    path.write_text("---\nname: n\ndescription: d\ncommand: c\n---\nbody", encoding="utf-8")
    metadata, body = WorkflowsEngine._parse_workflow_file(path)
    assert metadata.name == "n"
    assert metadata.description == "d"
    assert metadata.command == "c"
    assert body == "body"
