"""Alert evaluation and notification engine."""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from jarvis_core.obs import metrics
from jarvis_core.obs.alerts.schema import AlertRule, load_rules, save_rules


ALERT_STATE_PATH = Path("data/ops/alert_state.json")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _load_state() -> Dict[str, Any]:
    if not ALERT_STATE_PATH.exists():
        return {"last_sent": {}}
    with open(ALERT_STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_state(state: Dict[str, Any]) -> None:
    ALERT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERT_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _cooldown_ok(rule: AlertRule, state: Dict[str, Any]) -> bool:
    last_sent = _parse_ts(state.get("last_sent", {}).get(rule.rule_id))
    if not last_sent:
        return True
    return _now() - last_sent >= timedelta(minutes=rule.cooldown_minutes)


def _record_sent(rule: AlertRule, state: Dict[str, Any]) -> None:
    state.setdefault("last_sent", {})[rule.rule_id] = _now().isoformat()


def _load_jobs() -> List[Dict[str, Any]]:
    jobs_dir = Path("data/jobs")
    if not jobs_dir.exists():
        return []
    jobs = []
    for path in jobs_dir.glob("job_*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                jobs.append(json.load(f))
        except json.JSONDecodeError:
            continue
    return jobs


def _send_webhook(url: str, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as response:
        response.read()


def _dispatch_notifications(rule: AlertRule, payload: Dict[str, Any]) -> List[str]:
    sent = []
    for target in rule.notify:
        if target.startswith("webhook:"):
            webhook_url = os.getenv("OBS_WEBHOOK_URL") or os.getenv("JARVIS_WEBHOOK_URL")
            if webhook_url:
                _send_webhook(webhook_url, payload)
                sent.append(target)
    return sent


def _make_payload(rule: AlertRule, title: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "severity": rule.severity,
        "rule_id": rule.rule_id,
        "title": title,
        "message": message,
        "context": context,
    }


def evaluate_rules(rules: Optional[List[AlertRule]] = None) -> List[Dict[str, Any]]:
    rules = rules or load_rules()
    state = _load_state()
    sent_alerts = []

    metrics_summary = metrics.get_summary()
    run_metrics = metrics.get_run_metrics(days=7)
    counts_events = metrics.get_counts_events(days=7)
    jobs = _load_jobs()

    for rule in rules:
        if not rule.enabled or not _cooldown_ok(rule, state):
            continue

        condition_type = rule.condition.get("type")
        payload = None

        if condition_type == "cron_missing":
            minutes = int(rule.condition.get("minutes", 60))
            heartbeat_ts = _parse_ts(metrics_summary.get("last_cron_heartbeat_ts"))
            if not heartbeat_ts or _now() - heartbeat_ts > timedelta(minutes=minutes):
                payload = _make_payload(
                    rule,
                    "Cron heartbeat missing",
                    f"Cron heartbeat missing for {minutes} minutes",
                    {"last_cron_heartbeat_ts": metrics_summary.get("last_cron_heartbeat_ts")},
                )

        elif condition_type == "run_failed_burst":
            window = int(rule.condition.get("count", 5))
            threshold = float(rule.condition.get("failure_rate", 0.5))
            recent = run_metrics[-window:]
            if recent:
                failures = sum(1 for run in recent if run.get("status") == "failed")
                if failures / len(recent) >= threshold:
                    payload = _make_payload(
                        rule,
                        "Run failure burst",
                        f"{failures}/{len(recent)} runs failed in recent window",
                        {"window": len(recent), "failures": failures},
                    )

        elif condition_type == "run_stalled":
            minutes = int(rule.condition.get("minutes", 10))
            stalled = []
            cutoff = _now() - timedelta(minutes=minutes)
            for job in jobs:
                if job.get("status") != "running":
                    continue
                progress_ts = _parse_ts(job.get("progress_ts") or job.get("updated_at"))
                if progress_ts and progress_ts < cutoff:
                    stalled.append(job)
            if stalled:
                sample = stalled[0]
                payload = _make_payload(
                    rule,
                    "Run stalled",
                    f"{sample.get('job_id')} stalled for {minutes} minutes at step {sample.get('step')}",
                    {
                        "run_id": sample.get("job_id"),
                        "step": sample.get("step"),
                        "percent": sample.get("progress"),
                        "stalled_count": len(stalled),
                    },
                )

        elif condition_type == "oa_zero":
            window = int(rule.condition.get("count", 3))
            recent_counts = counts_events[-window:]
            if recent_counts and all(int(event.get("counts", {}).get("oa_count", 0)) == 0 for event in recent_counts):
                payload = _make_payload(
                    rule,
                    "OA count zero",
                    f"OA count was zero for {len(recent_counts)} runs",
                    {"window": len(recent_counts)},
                )

        elif condition_type == "submission_blocked":
            threshold = int(rule.condition.get("threshold", 5))
            blocked = metrics_summary.get("submission_blocked_count", 0)
            if blocked >= threshold:
                payload = _make_payload(
                    rule,
                    "Submission blocked",
                    f"Submission blocked count {blocked} exceeds threshold {threshold}",
                    {"submission_blocked_count": blocked},
                )

        if payload:
            _dispatch_notifications(rule, payload)
            _record_sent(rule, state)
            sent_alerts.append(payload)

    _save_state(state)
    return sent_alerts


def update_rules(rules_payload: List[Dict[str, Any]]) -> List[AlertRule]:
    rules = [AlertRule(**rule) for rule in rules_payload]
    save_rules(rules)
    return rules


def send_test_alert() -> Dict[str, Any]:
    rule = AlertRule(
        rule_id="test_alert",
        enabled=True,
        severity="low",
        condition={"type": "manual"},
        cooldown_minutes=0,
        notify=["webhook:primary"],
    )
    payload = _make_payload(rule, "Test alert", "This is a test alert", {"source": "api"})
    _dispatch_notifications(rule, payload)
    return payload
