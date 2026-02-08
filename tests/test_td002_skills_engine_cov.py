"""TD-002: Coverage tests for skills engine."""

from __future__ import annotations

from pathlib import Path

from jarvis_core.skills.engine import SkillsEngine
from jarvis_core.skills.schema import SkillScope


def _write_skill(
    base: Path,
    dir_name: str,
    *,
    frontmatter: str | None = None,
    body: str = "Default instructions",
) -> Path:
    skill_dir = base / ".agent" / "skills" / dir_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    if frontmatter:
        skill_file.write_text(f"---\n{frontmatter}\n---\n\n{body}\n", encoding="utf-8")
    else:
        skill_file.write_text(body + "\n", encoding="utf-8")
    return skill_dir


def test_engine_discovers_and_loads_skill_assets(tmp_path):
    workspace = Path(tmp_path)
    skill_dir = _write_skill(
        workspace,
        "qa-helper",
        frontmatter=(
            "name: QA Helper\n"
            "description: Helps with quality checks\n"
            "triggers:\n"
            "  - quality gate\n"
            "  - lint\n"
            "dependencies:\n"
            "  - pytest\n"
        ),
        body="Run lint and tests in order.",
    )
    (skill_dir / "resources").mkdir()
    (skill_dir / "resources" / "context.md").write_text("Context body", encoding="utf-8")
    (skill_dir / "scripts").mkdir()
    (skill_dir / "scripts" / "run.ps1").write_text("Write-Host test", encoding="utf-8")

    engine = SkillsEngine(workspace_path=workspace)
    listing = engine.list_all_skills()
    assert len(listing) == 1
    assert listing[0]["name"] == "QA Helper"
    assert listing[0]["scope"] == SkillScope.WORKSPACE.value
    assert listing[0]["loaded"] is False

    matches = engine.match_skills("Please run quality gate checks")
    assert matches == ["QA Helper"]

    resource = engine.get_resource("QA Helper", "context.md")
    assert resource == "Context body"

    context = engine.get_context_for_llm(["QA Helper"])
    assert "## Skill: QA Helper" in context
    assert "Run lint and tests in order." in context
    assert "### Resource: context.md" in context


def test_engine_handles_missing_skill_and_resource(tmp_path):
    workspace = Path(tmp_path)
    _write_skill(workspace, "simple", body="No frontmatter body")

    engine = SkillsEngine(workspace_path=workspace)
    assert engine.get_resource("missing", "none.txt") is None
    assert engine.get_context_for_llm(["missing"]) == ""

    listing = engine.list_all_skills()
    assert len(listing) == 1
    assert listing[0]["name"] == "simple"
    assert listing[0]["description"] == ""


def test_load_skill_is_noop_when_skill_file_missing(tmp_path):
    workspace = Path(tmp_path)
    skill_dir = workspace / ".agent" / "skills" / "broken"
    skill_dir.mkdir(parents=True, exist_ok=True)

    engine = SkillsEngine(workspace_path=workspace)
    engine._discover()
    # _discover() does not add entries when SKILL.md is missing.
    assert engine.list_all_skills() == []
