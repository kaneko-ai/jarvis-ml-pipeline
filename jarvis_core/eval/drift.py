"""Drift Detector.

Per RP-137, detects entity distribution drift between runs.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass


@dataclass
class DriftResult:
    """Result of drift detection."""

    current_run_id: str
    baseline_run_id: str
    kl_divergence: float
    js_divergence: float
    top_gains: list[tuple]  # (entity, delta)
    top_losses: list[tuple]  # (entity, delta)
    drifted: bool
    threshold: float


def entity_distribution(entities: list[str]) -> dict[str, float]:
    """Convert entity list to probability distribution."""
    if not entities:
        return {}

    counts = Counter(entities)
    total = sum(counts.values())

    return {entity: count / total for entity, count in counts.items()}


def kl_divergence(p: dict[str, float], q: dict[str, float]) -> float:
    """Calculate KL divergence D(P || Q).

    Note: Smooths Q to avoid division by zero.
    """
    if not p or not q:
        return 0.0

    all_keys = set(p.keys()) | set(q.keys())
    epsilon = 1e-10

    divergence = 0.0
    for key in all_keys:
        p_val = p.get(key, epsilon)
        q_val = q.get(key, epsilon)
        if p_val > 0:
            divergence += p_val * math.log(p_val / q_val)

    return max(0.0, divergence)


def js_divergence(p: dict[str, float], q: dict[str, float]) -> float:
    """Calculate Jensen-Shannon divergence.

    Symmetric and bounded [0, 1].
    """
    if not p or not q:
        return 0.0

    all_keys = set(p.keys()) | set(q.keys())

    # Calculate midpoint distribution
    m = {}
    for key in all_keys:
        m[key] = (p.get(key, 0.0) + q.get(key, 0.0)) / 2

    return (kl_divergence(p, m) + kl_divergence(q, m)) / 2


def detect_drift(
    current_entities: list[str],
    baseline_entities: list[str],
    current_run_id: str = "current",
    baseline_run_id: str = "baseline",
    threshold: float = 0.1,
) -> DriftResult:
    """Detect drift between current and baseline entity distributions.

    Args:
        current_entities: Entities from current run.
        baseline_entities: Entities from baseline run.
        current_run_id: ID of current run.
        baseline_run_id: ID of baseline run.
        threshold: JS divergence threshold for drift.

    Returns:
        DriftResult with divergence metrics and top changes.
    """
    current_dist = entity_distribution(current_entities)
    baseline_dist = entity_distribution(baseline_entities)

    kl = kl_divergence(current_dist, baseline_dist)
    js = js_divergence(current_dist, baseline_dist)

    # Find top gains (new or increased)
    gains = []
    for entity, current_prob in current_dist.items():
        baseline_prob = baseline_dist.get(entity, 0.0)
        delta = current_prob - baseline_prob
        if delta > 0:
            gains.append((entity, delta))
    gains.sort(key=lambda x: x[1], reverse=True)

    # Find top losses (removed or decreased)
    losses = []
    for entity, baseline_prob in baseline_dist.items():
        current_prob = current_dist.get(entity, 0.0)
        delta = baseline_prob - current_prob
        if delta > 0:
            losses.append((entity, delta))
    losses.sort(key=lambda x: x[1], reverse=True)

    return DriftResult(
        current_run_id=current_run_id,
        baseline_run_id=baseline_run_id,
        kl_divergence=kl,
        js_divergence=js,
        top_gains=gains[:5],
        top_losses=losses[:5],
        drifted=js > threshold,
        threshold=threshold,
    )


def format_drift_report(result: DriftResult) -> str:
    """Format drift result as human-readable report."""
    lines = []
    lines.append("# Drift Report")
    lines.append("")
    lines.append(f"**Baseline:** {result.baseline_run_id}")
    lines.append(f"**Current:** {result.current_run_id}")
    lines.append("")
    lines.append(f"**KL Divergence:** {result.kl_divergence:.4f}")
    lines.append(f"**JS Divergence:** {result.js_divergence:.4f}")
    lines.append(f"**Threshold:** {result.threshold:.4f}")
    lines.append("")

    if result.drifted:
        lines.append("⚠️ **DRIFT DETECTED**")
    else:
        lines.append("✓ No significant drift")

    lines.append("")

    if result.top_gains:
        lines.append("## Top Gains")
        for entity, delta in result.top_gains:
            lines.append(f"- {entity}: +{delta:.3f}")

    if result.top_losses:
        lines.append("")
        lines.append("## Top Losses")
        for entity, delta in result.top_losses:
            lines.append(f"- {entity}: -{delta:.3f}")

    return "\n".join(lines)
