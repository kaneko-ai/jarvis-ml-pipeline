"""Module Registry.

Per V4-P13, this provides discoverability for 128+ modules.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class ModuleInfo:
    """Module metadata."""

    name: str
    category: str
    description: str
    input_type: str
    output_type: str
    file_path: str


# Module registry
_MODULES: Dict[str, ModuleInfo] = {}


def register_module(
    name: str,
    category: str,
    description: str,
    input_type: str = "PaperVector[]",
    output_type: str = "dict",
    file_path: str = "",
) -> None:
    """Register a module."""
    _MODULES[name] = ModuleInfo(
        name=name,
        category=category,
        description=description,
        input_type=input_type,
        output_type=output_type,
        file_path=file_path,
    )


def get_module(name: str) -> Optional[ModuleInfo]:
    """Get module info by name."""
    return _MODULES.get(name)


def list_modules() -> List[str]:
    """List all module names."""
    return list(_MODULES.keys())


def list_by_category(category: str) -> List[str]:
    """List modules by category."""
    return [name for name, info in _MODULES.items() if info.category == category]


def get_categories() -> List[str]:
    """Get all categories."""
    return list(set(info.category for info in _MODULES.values()))


# Register core modules
def _init_registry():
    # Phase Ω modules
    register_module("autonomous_loop", "research_os", "Autonomous research loop", file_path="autonomous_loop.py")
    register_module("cross_field", "research_os", "Cross-field innovation", file_path="cross_field.py")
    register_module("failure_simulator", "research_os", "Failure simulation", file_path="failure_simulator.py")
    register_module("living_review", "research_os", "Living review generator", file_path="living_review.py")
    register_module("knowledge_graph", "research_os", "Knowledge graph", file_path="knowledge_graph.py")
    register_module("grant_optimizer", "research_os", "Grant optimization", file_path="grant_optimizer.py")
    register_module("reviewer_persona", "research_os", "Reviewer personas", file_path="reviewer_persona.py")
    register_module("lab_optimizer", "research_os", "Lab resource optimization", file_path="lab_optimizer.py")
    register_module("career_planner", "research_os", "Career planning", file_path="career_planner.py")
    register_module("pi_support", "research_os", "PI decision support", file_path="pi_support.py")

    # Phase Ψ modules
    register_module("roi_engine", "decision", "Research ROI calculation", file_path="roi_engine.py")
    register_module("negative_results", "decision", "Negative results vault", file_path="negative_results.py")
    register_module("reproducibility_cert", "decision", "Reproducibility certification", file_path="reproducibility_cert.py")
    register_module("lab_to_startup", "decision", "Lab to startup translation", file_path="lab_to_startup.py")
    register_module("clinical_readiness", "decision", "Clinical translation readiness", file_path="clinical_readiness.py")
    register_module("kill_switch", "decision", "Kill switch recommendation", file_path="kill_switch.py")
    register_module("student_portfolio", "decision", "Student portfolio management", file_path="student_portfolio.py")

    # Analysis modules
    register_module("gap_analysis", "analysis", "Research gap scoring", file_path="gap_analysis.py")
    register_module("hypothesis", "analysis", "Hypothesis generation", file_path="hypothesis.py")
    register_module("feasibility", "analysis", "Experiment feasibility", file_path="feasibility.py")
    register_module("paradigm", "analysis", "Paradigm shift detection", file_path="paradigm.py")
    register_module("heatmap", "analysis", "Concept heatmap", file_path="heatmap.py")

    # Paper vector modules
    register_module("recommendation", "paper_vector", "Paper recommendation", file_path="recommendation.py")
    register_module("comparison", "paper_vector", "Paper comparison", file_path="comparison.py")
    register_module("timeline", "paper_vector", "Timeline tracking", file_path="timeline.py")
    register_module("memory", "paper_vector", "Research memory", file_path="memory.py")

    # Workflows
    register_module("literature_to_plan", "workflow", "Literature to research plan", file_path="workflows/canonical.py")
    register_module("plan_to_grant", "workflow", "Plan to grant proposal", file_path="workflows/canonical.py")
    register_module("plan_to_paper", "workflow", "Plan to paper structure", file_path="workflows/canonical.py")
    register_module("plan_to_talk", "workflow", "Plan to presentation", file_path="workflows/canonical.py")


_init_registry()
