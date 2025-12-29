from datetime import datetime, timezone

from jarvis_core.scheduler import engine


def test_engine_due_and_next_run():
    schedule = {
        "schedule_id": "SCH_001",
        "enabled": True,
        "degraded": False,
        "name": "test",
        "timezone": "UTC",
        "rrule": "FREQ=DAILY;BYHOUR=0;BYMINUTE=0;BYSECOND=0",
        "created_at": "2024-01-01T00:00:00+00:00",
        "last_run_at": "2024-01-02T00:00:00+00:00",
    }
    now = datetime(2024, 1, 3, 1, 0, tzinfo=timezone.utc)
    assert engine.is_due(schedule, now, schedule.get("last_run_at"))
    next_run = engine.next_run_at(schedule, now=now)
    assert next_run.startswith("2024-01-04")
