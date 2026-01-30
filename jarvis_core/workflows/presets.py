"""Workflow Presets.

Per V4-P03, this provides preset configurations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkflowPreset:
    """Preset configuration for workflows."""

    name: str
    description: str
    workflow: str
    max_inputs: int = 1
    review_mode: bool = False
    depth: str = "standard"  # quick, standard, deep

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "workflow": self.workflow,
            "max_inputs": self.max_inputs,
            "review_mode": self.review_mode,
            "depth": self.depth,
        }


PRESETS = {
    "quick_plan": WorkflowPreset(
        name="quick_plan",
        description="Fast analysis with single PDF + query",
        workflow="literature_to_plan",
        max_inputs=1,
        review_mode=False,
        depth="quick",
    ),
    "deep_plan": WorkflowPreset(
        name="deep_plan",
        description="Comprehensive analysis with multiple inputs + review",
        workflow="literature_to_plan",
        max_inputs=10,
        review_mode=True,
        depth="deep",
    ),
    "grant_quick": WorkflowPreset(
        name="grant_quick",
        description="Quick grant proposal draft",
        workflow="plan_to_grant",
        max_inputs=3,
        depth="quick",
    ),
    "paper_structure": WorkflowPreset(
        name="paper_structure",
        description="Paper structure planning",
        workflow="plan_to_paper",
        max_inputs=5,
        depth="standard",
    ),
    "talk_prep": WorkflowPreset(
        name="talk_prep",
        description="Presentation preparation",
        workflow="plan_to_talk",
        max_inputs=3,
        depth="standard",
    ),
}


def get_preset(name: str) -> WorkflowPreset | None:
    """Get preset by name."""
    return PRESETS.get(name)


def list_presets() -> list[str]:
    """List available preset names."""
    return list(PRESETS.keys())


def apply_preset(preset_name: str) -> dict:
    """Get preset configuration as dict."""
    preset = get_preset(preset_name)
    if not preset:
        return {}
    return preset.to_dict()
