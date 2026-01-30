"""Workflows package."""

from .canonical import (
    run_literature_to_plan,
    run_plan_to_grant,
    run_plan_to_paper,
    run_plan_to_talk,
)
from .engine import WorkflowsEngine
from .schema import Workflow, WorkflowMetadata, WorkflowScope
from .slash_command import parse_slash_command

__all__ = [
    "run_literature_to_plan",
    "run_plan_to_grant",
    "run_plan_to_paper",
    "run_plan_to_talk",
    "WorkflowsEngine",
    "Workflow",
    "WorkflowMetadata",
    "WorkflowScope",
    "parse_slash_command",
]
