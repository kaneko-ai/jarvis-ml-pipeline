from __future__ import annotations

import os
from pathlib import Path

from jarvis_core.obs.alerts import engine as alert_engine
from jarvis_core.obs.alerts.schema import AlertRule, save_rules


def test_alert_cooldown(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data" / "ops").mkdir(parents=True, exist_ok=True)

    rules = [
        AlertRule(
            rule_id="cron_missing",
            enabled=True,
            severity="high",
            condition={"type": "cron_missing", "minutes": 0},
            cooldown_minutes=60,
            notify=["webhook:primary"],
        )
    ]
    save_rules(rules)

    first = alert_engine.evaluate_rules()
    second = alert_engine.evaluate_rules()

    assert len(first) == 1
    assert second == []
