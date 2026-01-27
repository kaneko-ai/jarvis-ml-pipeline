"""Workflow discovery and execution engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from jarvis_core.workflows.schema import Workflow, WorkflowMetadata, WorkflowScope


class WorkflowsEngine:
    """Discover and execute saved workflows."""

    def __init__(self, workspace_path: Path | None) -> None:
        self.workspace_path = workspace_path
        self._workflows: dict[str, Workflow] = {}

    def discover_workflows(self) -> None:
        """Discover global and workspace workflows."""
        workflows: dict[str, Workflow] = {}

        builtin_dir = Path(__file__).resolve().parent / "builtin"
        self._load_from_dir(builtin_dir, WorkflowScope.GLOBAL, workflows)

        global_dir = Path.home() / ".gemini" / "antigravity" / "global_workflows"
        self._load_from_dir(global_dir, WorkflowScope.GLOBAL, workflows)

        if self.workspace_path is not None:
            workspace_dir = self.workspace_path / ".agent" / "workflows"
            self._load_from_dir(workspace_dir, WorkflowScope.WORKSPACE, workflows)

        self._workflows = workflows

    def get_workflow(self, name: str) -> Workflow | None:
        """Return a workflow by name."""
        if not self._workflows:
            self.discover_workflows()
        return self._workflows.get(name)

    def list_workflows(self) -> list[dict[str, Any]]:
        """List workflows as dictionaries."""
        if not self._workflows:
            self.discover_workflows()
        return [
            {
                "name": wf.metadata.name,
                "description": wf.metadata.description,
                "command": wf.metadata.command,
                "scope": wf.scope.value,
                "path": wf.path,
            }
            for wf in self._workflows.values()
        ]

    def execute(self, name: str, context: dict[str, Any]) -> str:
        """Execute a workflow by returning its content with context."""
        workflow = self.get_workflow(name)
        if not workflow:
            raise ValueError(f"Workflow not found: {name}")
        context_block = yaml.safe_dump(context, sort_keys=False, allow_unicode=True)
        return f"{workflow.content}\n\n# Context\n{context_block}"

    def _load_from_dir(
        self, directory: Path, scope: WorkflowScope, workflows: dict[str, Workflow]
    ) -> None:
        if not directory.exists():
            return
        for path in directory.glob("*.md"):
            workflow = self._parse_workflow(path, scope)
            workflows[workflow.metadata.name] = workflow

    def _parse_workflow(self, path: Path, scope: WorkflowScope) -> Workflow:
        raw = path.read_text(encoding="utf-8")
        metadata, content = _split_frontmatter(raw)
        name = metadata.get("name") or path.stem
        description = metadata.get("description", "")
        command = metadata.get("command", "")
        return Workflow(
            metadata=WorkflowMetadata(
                name=name,
                description=description,
                command=command,
            ),
            scope=scope,
            path=str(path),
            content=content.strip(),
        )


def _split_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            metadata = yaml.safe_load(parts[1]) or {}
            return metadata, parts[2].lstrip()
    return {}, raw
