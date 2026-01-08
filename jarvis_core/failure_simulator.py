"""Failure-Aware Research Simulator.

Per Issue Ω-7, this simulates research failure branches.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def simulate_failure_tree(
    hypothesis: str,
    vectors: list[PaperVector],
    max_depth: int = 3,
) -> dict:
    """Simulate failure branching tree for a hypothesis.

    Args:
        hypothesis: Hypothesis to simulate.
        vectors: Context vectors.
        max_depth: Maximum tree depth.

    Returns:
        Failure tree dict.
    """
    if not hypothesis:
        return {"hypothesis": "", "branches": [], "estimated": True}

    branches = _generate_failure_branches(hypothesis, vectors, depth=0, max_depth=max_depth)

    # Calculate overall risk
    total_branches = _count_branches(branches)
    failure_probability = min(0.9, 0.3 + 0.1 * total_branches)

    return {
        "hypothesis": hypothesis,
        "branches": branches,
        "total_failure_paths": total_branches,
        "overall_failure_probability": round(failure_probability, 2),
        "mitigation_strategies": _suggest_mitigations(branches),
        "estimated": True,  # Always mark as estimated
    }


def _generate_failure_branches(
    hypothesis: str,
    vectors: list[PaperVector],
    depth: int,
    max_depth: int,
) -> list[dict]:
    """Generate failure branches recursively."""
    if depth >= max_depth:
        return []

    hypothesis_lower = hypothesis.lower()
    branches = []

    # Technical failure
    branches.append({
        "type": "technical",
        "description": "実験技術的失敗",
        "probability": 0.3,
        "sub_branches": [
            {"type": "sub", "description": "プロトコル最適化失敗", "probability": 0.4},
            {"type": "sub", "description": "試薬品質問題", "probability": 0.2},
        ] if depth < max_depth - 1 else [],
    })

    # Biological failure
    if "immune" in hypothesis_lower or "cell" in hypothesis_lower:
        branches.append({
            "type": "biological",
            "description": "生物学的変動",
            "probability": 0.4,
            "sub_branches": [
                {"type": "sub", "description": "細胞ロット変動", "probability": 0.3},
                {"type": "sub", "description": "マウス系統差", "probability": 0.25},
            ] if depth < max_depth - 1 else [],
        })

    # Conceptual failure
    branches.append({
        "type": "conceptual",
        "description": "仮説自体の誤り",
        "probability": 0.2,
        "sub_branches": [
            {"type": "sub", "description": "前提条件の誤認", "probability": 0.5},
            {"type": "sub", "description": "相関と因果の混同", "probability": 0.3},
        ] if depth < max_depth - 1 else [],
    })

    # Resource failure
    branches.append({
        "type": "resource",
        "description": "リソース不足",
        "probability": 0.15,
        "sub_branches": [] if depth < max_depth - 1 else [],
    })

    return branches


def _count_branches(branches: list[dict]) -> int:
    """Count total branches in tree."""
    count = len(branches)
    for b in branches:
        count += _count_branches(b.get("sub_branches", []))
    return count


def _suggest_mitigations(branches: list[dict]) -> list[str]:
    """Suggest mitigation strategies."""
    mitigations = []

    for b in branches:
        if b["type"] == "technical":
            mitigations.append("プロトコルのパイロットスタディ実施")
        elif b["type"] == "biological":
            mitigations.append("複数ロット/系統での再現性確認")
        elif b["type"] == "conceptual":
            mitigations.append("ネガティブコントロールの充実")
        elif b["type"] == "resource":
            mitigations.append("段階的実験計画の策定")

    return list(set(mitigations))


def get_critical_failure_path(tree: dict) -> list[str]:
    """Get the most likely failure path."""
    path = []
    branches = tree.get("branches", [])

    while branches:
        # Find highest probability branch
        highest = max(branches, key=lambda x: x.get("probability", 0))
        path.append(highest["description"])
        branches = highest.get("sub_branches", [])

    return path
