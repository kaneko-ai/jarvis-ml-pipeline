"""Alert schema and persistence helpers."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ALERT_RULES_PATH = Path("data/ops/alert_rules.json")


@dataclass
class AlertRule:
    rule_id: str
    enabled: bool
    severity: str
    condition: dict[str, Any]
    cooldown_minutes: int
    notify: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_rules() -> list[AlertRule]:
    return [
        AlertRule(
            rule_id="cron_missing",
            enabled=True,
            severity="high",
            condition={"type": "cron_missing", "minutes": 60},
            cooldown_minutes=60,
            notify=["webhook:primary"],
        ),
        AlertRule(
            rule_id="run_failed_burst",
            enabled=True,
            severity="high",
            condition={"type": "run_failed_burst", "count": 5, "failure_rate": 0.5},
            cooldown_minutes=30,
            notify=["webhook:primary"],
        ),
        AlertRule(
            rule_id="run_stalled",
            enabled=True,
            severity="high",
            condition={"type": "run_stalled", "minutes": 10},
            cooldown_minutes=30,
            notify=["webhook:primary"],
        ),
        AlertRule(
            rule_id="oa_zero",
            enabled=True,
            severity="medium",
            condition={"type": "oa_zero", "count": 3},
            cooldown_minutes=60,
            notify=["webhook:primary"],
        ),
        AlertRule(
            rule_id="submission_blocked",
            enabled=True,
            severity="medium",
            condition={"type": "submission_blocked", "threshold": 5},
            cooldown_minutes=60,
            notify=["webhook:primary"],
        ),
    ]


def load_rules() -> list[AlertRule]:
    if not ALERT_RULES_PATH.exists():
        rules = default_rules()
        save_rules(rules)
        return rules
    with open(ALERT_RULES_PATH, encoding="utf-8") as f:
        payload = json.load(f)
    return [AlertRule(**rule) for rule in payload.get("rules", [])]


def save_rules(rules: list[AlertRule]) -> None:
    ALERT_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERT_RULES_PATH, "w", encoding="utf-8") as f:
        json.dump({"rules": [rule.to_dict() for rule in rules]}, f, ensure_ascii=False, indent=2)
