"""Explainable feedback risk model."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import yaml

from .schema import FeedbackEntry


@dataclass
class RiskResult:
    location: dict[str, int]
    risk_score: float
    risk_level: str
    top_categories: list[dict[str, float]]
    reasons: list[str]


class FeedbackRiskModel:
    """Rule-weighted risk model with explanations."""

    def __init__(self, config_path: str = "data/feedback/risk_model.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def score(
        self,
        features: dict[str, float],
        history: list[FeedbackEntry],
        section: str = "unknown",
    ) -> dict[str, object]:
        base = self.config.get("base", 0.0)
        weights = self.config.get("weights", {})
        linear = base
        reasons: list[str] = []

        for key, weight in weights.items():
            value = features.get(key, 0.0)
            if value:
                linear += weight * value
                reasons.append(self._reason_from_feature(key, value))

        history_reasons, history_bias = self._history_bias(history, section)
        linear += history_bias
        reasons.extend(history_reasons)

        score = 1 / (1 + math.exp(-linear))
        risk_level = self._risk_level(score)
        categories = self._category_probs(features, history)

        return {
            "risk_score": round(score, 2),
            "risk_level": risk_level,
            "top_categories": categories,
            "reasons": [r for r in reasons if r],
        }

    def ready_threshold(self) -> int:
        return int(self.config.get("ready_high_limit", 1))

    def _risk_level(self, score: float) -> str:
        thresholds = self.config.get("thresholds", {"high": 0.75, "medium": 0.45})
        if score >= thresholds.get("high", 0.75):
            return "high"
        if score >= thresholds.get("medium", 0.45):
            return "medium"
        return "low"

    def _category_probs(
        self,
        features: dict[str, float],
        history: list[FeedbackEntry],
    ) -> list[dict[str, float]]:
        category_rules = self.config.get("category_rules", {})
        scores = {category: rule.get("base", 0.1) for category, rule in category_rules.items()}

        for category, rule in category_rules.items():
            for feature_key, weight in rule.get("features", {}).items():
                if features.get(feature_key, 0.0):
                    scores[category] = scores.get(category, 0.1) + weight

        for entry in history:
            scores[entry.category] = scores.get(entry.category, 0.1) + 0.15

        total = sum(scores.values()) or 1.0
        normalized = [
            {"category": key, "prob": round(value / total, 2)}
            for key, value in sorted(scores.items(), key=lambda item: item[1], reverse=True)
        ]
        return normalized[:3]

    def _history_bias(self, history: list[FeedbackEntry], section: str) -> tuple[list[str], float]:
        reasons: list[str] = []
        bias = 0.0
        if not history:
            return reasons, bias
        same_section = [h for h in history if h.location.type == "paragraph"]
        if same_section:
            reasons.append(f"過去{len(same_section)}回、同タイプ箇所で指摘が発生")
            bias += min(0.4, 0.1 * len(same_section))
        return reasons, bias

    def _reason_from_feature(self, key: str, value: float) -> str | None:
        mapping = {
            "error_count": f"P6 lint errorが{int(value)}件あります",
            "warn_count": f"P6 lint warningが{int(value)}件あります",
            "ambiguous_count": f"曖昧語が{int(value)}件含まれています",
            "weak_evidence": "根拠表現が不足しています",
            "subject_missing": "主語が明示されていない文が多い可能性があります",
            "causal_present": "因果表現が使われています（根拠の明示が必要）",
        }
        return mapping.get(key)

    def _load_config(self) -> dict[str, object]:
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {
            "base": 0.0,
            "weights": {},
            "thresholds": {"high": 0.75, "medium": 0.45},
        }