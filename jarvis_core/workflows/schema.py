"""Workflow schema definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class WorkflowScope(str, Enum):
    """Scope for a workflow definition."""

    GLOBAL = "global"
    WORKSPACE = "workspace"


@dataclass
class WorkflowMetadata:
    """Metadata for workflow frontmatter."""

    name: str
    description: str
    command: str


@dataclass
class Workflow:
    """Loaded workflow definition."""

    metadata: WorkflowMetadata
    scope: WorkflowScope
    path: Path
    content: str