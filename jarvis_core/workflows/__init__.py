"""Workflows package."""

from .canonical import (
    run_literature_to_plan,
    run_plan_to_grant,
    run_plan_to_paper,
    run_plan_to_talk,
)

__all__ = [
    "run_literature_to_plan",
    "run_plan_to_grant",
    "run_plan_to_paper",
    "run_plan_to_talk",
]
