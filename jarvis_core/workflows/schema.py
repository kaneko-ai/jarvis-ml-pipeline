"""Schema definitions for workflows."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorkflowScope(str, Enum):
    """Workflow scope values."""

    GLOBAL = "global"
    WORKSPACE = "workspace"


@dataclass
class WorkflowMetadata:
    """Metadata for a workflow."""

    name: str
    description: str
    command: str


@dataclass
class Workflow:
    """Workflow definition."""

    metadata: WorkflowMetadata
    scope: WorkflowScope
    path: str
    content: str
