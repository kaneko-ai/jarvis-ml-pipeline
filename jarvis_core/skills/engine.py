"""Core engine for discovering and loading skills."""
from __future__ import annotations

import textwrap
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from .schema import Skill, SkillMetadata, SkillScope


class SkillsEngine:
    """Discover, match, and load skills from configured directories."""

    def __init__(self, workspace_path: Path | None = None) -> None:
        self.workspace_path = Path(workspace_path) if workspace_path else None
        self._skills: dict[str, Skill] = {}
        self._discovered = False

    def _skill_dirs(self) -> list[tuple[SkillScope, Path]]:
        dirs: list[tuple[SkillScope, Path]] = [
            (SkillScope.GLOBAL, Path("~/.gemini/antigravity/skills").expanduser()),
        ]
        if self.workspace_path:
            dirs.append((SkillScope.WORKSPACE, self.workspace_path / ".agent" / "skills"))
        return dirs

    def _discover(self) -> None:
        if self._discovered:
            return
        for scope, base_dir in self._skill_dirs():
            if not base_dir.exists():
                continue
            for skill_file in base_dir.rglob("SKILL.md"):
                metadata, _ = self._parse_skill_file(skill_file)
                skill_name = metadata.name
                self._skills[skill_name] = Skill(
                    metadata=metadata,
                    scope=scope,
                    path=skill_file.parent,
                )
        self._discovered = True

    def _parse_skill_file(self, path: Path) -> tuple[SkillMetadata, str]:
        content = path.read_text(encoding="utf-8")
        frontmatter: dict[str, Any] = {}
        body = content
        lines = content.splitlines()
        if lines and lines[0].strip() == "---":
            end_index = None
            for idx in range(1, len(lines)):
                if lines[idx].strip() == "---":
                    end_index = idx
                    break
            if end_index is not None:
                frontmatter_text = "\n".join(lines[1:end_index])
                frontmatter = yaml.safe_load(frontmatter_text) or {}
                body = "\n".join(lines[end_index + 1 :]).lstrip()
        metadata = SkillMetadata(
            name=str(frontmatter.get("name") or path.parent.name),
            description=str(frontmatter.get("description") or ""),
            triggers=list(frontmatter.get("triggers") or []),
            dependencies=list(frontmatter.get("dependencies") or []),
        )
        return metadata, body

    def _load_skill(self, skill: Skill) -> None:
        if skill.loaded:
            return
        skill_file = skill.path / "SKILL.md"
        if not skill_file.exists():
            return
        metadata, body = self._parse_skill_file(skill_file)
        skill.metadata = metadata
        skill.instructions = body
        resources_dir = skill.path / "resources"
        if resources_dir.exists():
            for resource in resources_dir.iterdir():
                if resource.is_file():
                    skill.resources[resource.name] = resource.read_text(encoding="utf-8")
        scripts_dir = skill.path / "scripts"
        if scripts_dir.exists():
            for script in scripts_dir.iterdir():
                if script.is_file():
                    skill.scripts[script.name] = script.read_text(encoding="utf-8")
        skill.loaded = True

    def list_all_skills(self) -> list[dict]:
        self._discover()
        output = []
        for skill in self._skills.values():
            data = asdict(skill.metadata)
            data.update(
                {
                    "scope": skill.scope.value,
                    "path": str(skill.path),
                    "loaded": skill.loaded,
                }
            )
            output.append(data)
        return sorted(output, key=lambda item: item.get("name", ""))

    def match_skills(self, user_request: str) -> list[str]:
        self._discover()
        normalized = user_request.lower()
        matches: list[str] = []
        for name, skill in self._skills.items():
            triggers = [trigger.lower() for trigger in skill.metadata.triggers]
            if any(trigger in normalized for trigger in triggers if trigger):
                matches.append(name)
        return sorted(set(matches))

    def get_resource(self, skill_name: str, resource_name: str) -> str | None:
        self._discover()
        skill = self._skills.get(skill_name)
        if not skill:
            return None
        if not skill.loaded:
            self._load_skill(skill)
        return skill.resources.get(resource_name)

    def get_context_for_llm(self, skill_names: list[str]) -> str:
        self._discover()
        sections: list[str] = []
        for skill_name in skill_names:
            skill = self._skills.get(skill_name)
            if not skill:
                continue
            self._load_skill(skill)
            header = f"## Skill: {skill.metadata.name}\n{skill.metadata.description}".strip()
            section_parts = [header]
            if skill.instructions:
                section_parts.append(skill.instructions.strip())
            if skill.resources:
                resources_text = [
                    f"### Resource: {name}\n{content.strip()}"
                    for name, content in skill.resources.items()
                ]
                section_parts.append("\n\n".join(resources_text))
            sections.append("\n\n".join(section_parts))
        return textwrap.dedent("\n\n".join(sections)).strip()
