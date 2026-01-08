"""Lab Resource Optimizer.

Per Issue Ω-4, this optimizes lab resource allocation.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


# Common lab resources
LAB_RESOURCES = {
    "flow_cytometer": {"methods": ["FACS", "flow cytometry"], "cost": 0.6},
    "sequencer": {"methods": ["scRNA-seq", "RNA-seq"], "cost": 0.9},
    "microscope": {"methods": ["imaging", "confocal"], "cost": 0.5},
    "pcr_machine": {"methods": ["qPCR", "PCR"], "cost": 0.2},
    "western_setup": {"methods": ["Western blot"], "cost": 0.3},
    "animal_facility": {"methods": ["mouse model", "in vivo"], "cost": 0.8},
    "crispr_setup": {"methods": ["CRISPR", "knockout"], "cost": 0.7},
}


def optimize_lab_resources(
    hypothesis: str,
    vectors: list[PaperVector],
    available_resources: list[str] | None = None,
) -> dict:
    """Optimize lab resource allocation for a hypothesis.

    Args:
        hypothesis: The hypothesis to test.
        vectors: Context vectors.
        available_resources: List of available resource IDs.

    Returns:
        Resource optimization plan.
    """
    if not hypothesis:
        return {
            "required_resources": [],
            "path": [],
            "estimated_cost": 0.0,
        }

    # Find required methods from related papers
    hypothesis_lower = hypothesis.lower()
    required_methods = set()

    for v in vectors:
        for c in v.concept.concepts:
            if c.lower() in hypothesis_lower or hypothesis_lower in c.lower():
                required_methods.update(v.method.methods.keys())
                break

    if not required_methods:
        # Default methods
        required_methods = {"Western blot", "qPCR"}

    # Map methods to resources
    required_resources = []
    for res_id, res_info in LAB_RESOURCES.items():
        for method in required_methods:
            if method in res_info["methods"]:
                required_resources.append({
                    "resource": res_id,
                    "for_method": method,
                    "cost": res_info["cost"],
                })
                break

    # Filter by availability
    if available_resources:
        available_set = set(available_resources)
        required_resources = [
            r for r in required_resources
            if r["resource"] in available_set
        ]

    # Build optimal path (simple: sort by cost)
    required_resources.sort(key=lambda x: x["cost"])

    path = [r["resource"] for r in required_resources]
    total_cost = sum(r["cost"] for r in required_resources)

    return {
        "required_resources": required_resources,
        "path": path,
        "estimated_cost": round(total_cost, 2),
        "required_methods": list(required_methods),
        "missing_resources": _find_missing_resources(required_methods, available_resources),
    }


def _find_missing_resources(
    methods: set,
    available: list[str] | None,
) -> list[str]:
    """Find resources needed but not available."""
    if available is None:
        return []

    available_set = set(available)
    needed = set()

    for method in methods:
        for res_id, res_info in LAB_RESOURCES.items():
            if method in res_info["methods"]:
                needed.add(res_id)

    return list(needed - available_set)
