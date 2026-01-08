"""Risk factor definitions for decision intelligence."""

from __future__ import annotations

from dataclasses import dataclass

from .schema import RationaleValue, RiskFactorInput


@dataclass(frozen=True)
class RiskFactorDefinition:
    name: str
    description: str


DEFAULT_RISK_FACTORS: list[RiskFactorDefinition] = [
    RiskFactorDefinition("Technical Risk", "技術難度・実装の不確実性"),
    RiskFactorDefinition("Data Risk", "データが得られない確率"),
    RiskFactorDefinition("Resource Risk", "設備・試薬・計算資源の不足"),
    RiskFactorDefinition("Competitive Risk", "競合の強さ・先行"),
    RiskFactorDefinition("Guidance Risk", "指導・方向づけの不足"),
    RiskFactorDefinition("Time Risk", "期限・スケジュール超過"),
    RiskFactorDefinition("Personal Risk", "体力・集中・メンタル（自己申告）"),
]


def default_risk_inputs() -> list[RiskFactorInput]:
    """Create default risk factor inputs with neutral values."""
    default_score = RationaleValue(
        value=0.5,
        rationale="（推測です）入力未設定のため中立値を採用",
    )
    default_weight = RationaleValue(
        value=1.0,
        rationale="（推測です）標準重み",
    )
    return [
        RiskFactorInput(
            name=factor.name,
            score=default_score,
            weight=default_weight,
            rationale=factor.description,
        )
        for factor in DEFAULT_RISK_FACTORS
    ]
