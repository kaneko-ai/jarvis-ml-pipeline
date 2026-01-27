"""Workflows engine for discovery and execution."""

from __future__ import annotations

import json
import textwrap
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from .schema import Workflow, WorkflowMetadata, WorkflowScope


class WorkflowsEngine:
    """Discover and execute saved workflows."""

    def __init__(self, workspace_path: Path | None) -> None:
        self.workspace_path = Path(workspace_path) if workspace_path else None
        self._workflows: dict[str, Workflow] = {}
        self._discovered = False

    def discover_workflows(self) -> None:
        if self._discovered:
            return
        for scope, base_dir in self._workflow_dirs():
            if not base_dir.exists():
                continue
            for workflow_file in sorted(base_dir.rglob("*.md")):
                metadata, body = self._parse_workflow_file(workflow_file)
                workflow = Workflow(
                    metadata=metadata,
                    scope=scope,
                    path=workflow_file,
                    content=body,
                )
                self._workflows[metadata.name] = workflow
        self._discovered = True

    def get_workflow(self, name: str) -> Workflow | None:
        self.discover_workflows()
        return self._workflows.get(name)

    def list_workflows(self) -> list[dict]:
        self.discover_workflows()
        output = []
        for workflow in self._workflows.values():
            data = asdict(workflow.metadata)
            data.update(
                {
                    "scope": workflow.scope.value,
                    "path": str(workflow.path),
                }
            )
            output.append(data)
        return sorted(output, key=lambda item: item.get("name", ""))

    def execute(self, name: str, context: dict) -> str:
        workflow = self.get_workflow(name)
        if not workflow:
            raise ValueError(f"Workflow not found: {name}")
        payload = json.dumps(context, ensure_ascii=False, indent=2)
        execution = """# Workflow Execution

## Workflow
{workflow_name}

## Description
{description}

## Context
{context}

## Steps
{steps}
""".format(
            workflow_name=workflow.metadata.name,
            description=workflow.metadata.description,
            context=payload,
            steps=workflow.content.strip(),
        )
        return textwrap.dedent(execution).strip()

    def _workflow_dirs(self) -> list[tuple[WorkflowScope, Path]]:
        dirs = [
            (WorkflowScope.GLOBAL, Path("~/.gemini/antigravity/global_workflows").expanduser()),
            (WorkflowScope.GLOBAL, Path(__file__).parent / "builtin"),
        ]
        if self.workspace_path:
            dirs.append((WorkflowScope.WORKSPACE, self.workspace_path / ".agent" / "workflows"))
        return dirs

    @staticmethod
    def _parse_workflow_file(path: Path) -> tuple[WorkflowMetadata, str]:
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
        metadata = WorkflowMetadata(
            name=str(frontmatter.get("name") or path.stem),
            description=str(frontmatter.get("description") or ""),
            command=str(frontmatter.get("command") or ""),
        )
        return metadata, body
