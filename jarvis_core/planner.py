"""Minimal task planner for Jarvis Core.

The planner expands a high-level :class:`~jarvis_core.task.Task` into
an ordered list of executable subtasks using simple, category-specific
recipes. Categories without a defined recipe fall back to returning the
root task as-is to keep behavior safe and predictable.
"""
from __future__ import annotations

from copy import deepcopy
from typing import List

from .task import Task, TaskCategory, TaskStatus


class Planner:
    """Rule-based planner that expands tasks into ordered subtasks."""

    _RECIPES = {
        TaskCategory.PAPER_SURVEY: [
            "Clarify paper requirements and search keywords",
            "Collect candidate papers or sources",
            "Summarize findings against the goal",
        ],
        TaskCategory.THESIS: [
            "Outline key sections to address the goal",
            "Gather supporting references or figures",
            "Draft cohesive text for the thesis section",
        ],
        TaskCategory.JOB_HUNTING: [
            "Clarify role and company expectations",
            "Draft or refine job-hunting materials",
            "Review and polish wording for clarity",
        ],
    }

    def plan(self, task: Task) -> List[Task]:
        """Expand a root task into an ordered list of subtasks.

        If a category recipe exists, generate one subtask per step using the
        root task as context. Otherwise, return the original task wrapped in a
        list to maintain safe behavior.
        """

        recipe = self._RECIPES.get(task.category)
        if not recipe:
            return [task]

        subtasks: List[Task] = []
        for idx, step in enumerate(recipe, start=1):
            subtask = Task(
                task_id=f"{task.task_id}:{idx}",
                title=f"{task.title} — {step}",
                category=task.category,
                user_goal=task.user_goal,
                inputs=deepcopy(task.inputs),
                constraints=deepcopy(task.constraints),
                priority=task.priority,
                status=TaskStatus.PENDING,
            )
            subtask.history.append({
                "event": "planned",
                "step": idx,
                "description": step,
                "source_task": task.task_id,
            })
            subtasks.append(subtask)

        task.history.append({
            "event": "plan_generated",
            "subtasks": [s.task_id for s in subtasks],
        })
        return subtasks
