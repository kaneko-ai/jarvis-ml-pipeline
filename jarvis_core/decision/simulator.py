"""Monte Carlo simulator for decision outcomes."""
from __future__ import annotations

import math
import random

from .risk_factors import default_risk_inputs
from .schema import Assumption, Option

TASK_KEYWORDS = {
    "setup": ["立ち上げ", "setup", "環境", "構築"],
    "data_collection": ["データ", "収集", "in vivo", "実験"],
    "analysis": ["解析", "analysis", "bioinformatics"],
    "writing": ["執筆", "writing", "投稿"],
    "revision": ["改訂", "revision", "review"],
}


def sample_distribution(distribution) -> float:
    """Sample from a distribution definition."""
    if distribution.type == "triangular":
        return random.triangular(
            distribution.low.value,
            distribution.high.value,
            distribution.mode.value,
        )
    if distribution.type == "normal":
        return max(0.0, random.gauss(distribution.mean.value, distribution.std.value))
    if distribution.type == "lognormal":
        return random.lognormvariate(distribution.mean.value, distribution.sigma.value)
    raise ValueError(f"Unsupported distribution type: {distribution.type}")


def _assign_task(assumption: Assumption) -> str:
    name = assumption.name.lower()
    for task, keywords in TASK_KEYWORDS.items():
        if any(keyword.lower() in name for keyword in keywords):
            return task
    return "general"


def _weighted_risk(option: Option) -> tuple[float, list[dict[str, float]]]:
    risk_inputs = option.risk_factors or default_risk_inputs()
    total_weight = sum(risk.weight.value for risk in risk_inputs) or 1.0
    weighted_score = sum(risk.score.value * risk.weight.value for risk in risk_inputs) / total_weight
    contributions = []
    for risk in risk_inputs:
        contribution = (risk.score.value * risk.weight.value) / total_weight
        contributions.append(
            {
                "name": risk.name,
                "contribution": contribution,
                "score": risk.score.value,
                "weight": risk.weight.value,
            }
        )
    return weighted_score, contributions


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    rank = (percentile / 100) * (len(sorted_values) - 1)
    low_index = math.floor(rank)
    high_index = math.ceil(rank)
    if low_index == high_index:
        return sorted_values[int(rank)]
    weight = rank - low_index
    return sorted_values[low_index] * (1 - weight) + sorted_values[high_index] * weight


def _correlation(xs: list[float], ys: list[int]) -> float:
    if not xs or not ys:
        return 0.0
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    variance_x = sum((x - mean_x) ** 2 for x in xs)
    variance_y = sum((y - mean_y) ** 2 for y in ys)
    if variance_x == 0 or variance_y == 0:
        return 0.0
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return covariance / math.sqrt(variance_x * variance_y)


def simulate_option(
    option: Option,
    assumptions: list[Assumption],
    iterations: int = 5000,
) -> dict[str, object]:
    """Simulate an option and return Monte Carlo results."""
    task_samples: dict[str, list[float]] = {}
    assumption_samples: dict[str, list[float]] = {a.assumption_id: [] for a in assumptions}
    successes: list[int] = []
    success_scores: list[float] = []
    papers: list[float] = []
    presentations: list[float] = []

    risk_score, contributions = _weighted_risk(option)

    for _ in range(iterations):
        total_time = 0.0
        for assumption in assumptions:
            sample = sample_distribution(assumption.distribution)
            assumption_samples[assumption.assumption_id].append(sample)
            total_time += sample
            task = _assign_task(assumption)
            task_samples.setdefault(task, []).append(sample)

        risk_multiplier = 1.0 + 0.5 * risk_score
        total_time *= risk_multiplier

        horizon = option.time_horizon_months.value
        time_gap = max(0.0, total_time - horizon)
        time_score = max(0.0, 1 - (time_gap / max(horizon, 1.0)))
        base_success = (0.6 * time_score) + (0.4 * (1 - risk_score))
        base_success = max(0.0, min(1.0, base_success))
        success_scores.append(base_success)
        success = 1 if random.random() < base_success else 0
        successes.append(success)

        papers.append(max(0.0, success * max(1.0, total_time / 18)))
        presentations.append(max(0.0, success * max(1.0, total_time / 12)))

    success_rate = sum(successes) / len(successes) if successes else 0.0

    sensitivity = []
    for assumption in assumptions:
        corr = abs(_correlation(assumption_samples[assumption.assumption_id], successes))
        sensitivity.append(
            {
                "assumption_id": assumption.assumption_id,
                "name": assumption.name,
                "impact_score": corr,
            }
        )
    sensitivity.sort(key=lambda item: item["impact_score"], reverse=True)

    skill_attainment = {}
    for skill in option.dependencies.must_learn:
        attainment = max(0.0, min(1.0, 0.4 + 0.6 * success_rate - 0.3 * risk_score))
        skill_attainment[skill] = attainment

    return {
        "success_rate": success_rate,
        "success_range": {
            "p10": _percentile(success_scores, 10),
            "p50": _percentile(success_scores, 50),
            "p90": _percentile(success_scores, 90),
        },
        "papers_range": {
            "p10": _percentile(papers, 10),
            "p50": _percentile(papers, 50),
            "p90": _percentile(papers, 90),
        },
        "presentations_range": {
            "p10": _percentile(presentations, 10),
            "p50": _percentile(presentations, 50),
            "p90": _percentile(presentations, 90),
        },
        "contributions": contributions,
        "sensitivity": sensitivity[:5],
        "skill_attainment": skill_attainment,
    }
