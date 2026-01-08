"""Elicitation helper for decision inputs."""
from __future__ import annotations

from pydantic import ValidationError

from .risk_factors import DEFAULT_RISK_FACTORS, default_risk_inputs
from .schema import DecisionInput, Option


def template_payload() -> dict[str, object]:
    """Return a template payload for decision input."""
    return {
        "options": [
            {
                "option_id": "A",
                "label": "京都大 CCII 茶本研（例）",
                "goal": "博士課程で第一著者論文1本/学位取得",
                "theme": "がん免疫×代謝×抗体（例）",
                "time_horizon_months": {
                    "value": 36,
                    "rationale": "（推測です）博士課程の想定期間",
                },
                "constraints": {
                    "weekly_hours": {
                        "value": 60,
                        "rationale": "（推測です）研究時間の想定",
                    },
                    "budget_level": "medium",
                    "equipment_access": "high",
                    "mentor_support": "high",
                },
                "dependencies": {
                    "must_learn": ["in vivo", "scRNA-seq", "bioinformatics"],
                    "must_access": ["mouse facility", "flow core"],
                },
                "risk_factors": [
                    {
                        "name": factor.name,
                        "score": {
                            "value": 0.5,
                            "rationale": "（推測です）入力未設定のため中立",
                        },
                        "weight": {
                            "value": 1.0,
                            "rationale": "（推測です）標準重み",
                        },
                        "rationale": factor.description,
                    }
                    for factor in DEFAULT_RISK_FACTORS
                ],
            }
        ],
        "assumptions": [
            {
                "assumption_id": "A1",
                "name": "主要実験の立ち上げ期間",
                "distribution": {
                    "type": "triangular",
                    "low": {"value": 2, "rationale": "（推測です）最低期間"},
                    "mode": {"value": 4, "rationale": "（推測です）一般的期間"},
                    "high": {"value": 8, "rationale": "（推測です）最長期間"},
                    "unit": "months",
                },
                "rationale": "（推測です）過去類似プロジェクトの一般的目安",
                "applies_to": "setup",
            }
        ],
        "risk_factors": [
            {
                "name": factor.name,
                "description": factor.description,
            }
            for factor in DEFAULT_RISK_FACTORS
        ],
        "disclaimer": "仮定に依存する（推測です）",
    }


def validate_payload(payload: dict[str, object]) -> dict[str, object]:
    """Validate payload and return either parsed data or errors."""
    try:
        parsed = DecisionInput.parse_obj(payload)
        return {
            "valid": True,
            "errors": [],
            "parsed": parsed,
        }
    except ValidationError as exc:
        return {
            "valid": False,
            "errors": exc.errors(),
            "parsed": None,
        }


def normalize_risks(options: list[Option]) -> list[Option]:
    """Ensure each option has risk factors populated."""
    normalized = []
    for option in options:
        if option.risk_factors:
            normalized.append(option)
        else:
            option.risk_factors = default_risk_inputs()
            normalized.append(option)
    return normalized
