from datetime import datetime, timezone

from jarvis_core.scheduler import idempotency, locks


def test_idempotency_key_stable():
    schedule = {
        "schedule_id": "SCH_123",
        "rrule": "FREQ=DAILY;BYHOUR=0;BYMINUTE=0;BYSECOND=0",
        "timezone": "UTC",
        "query": {"keywords": ["CD73"], "oa_only": True},
    }
    now = datetime(2024, 1, 3, 10, 0, tzinfo=timezone.utc)
    key1 = idempotency.idempotency_key(schedule, now)
    key2 = idempotency.idempotency_key(schedule, now)
    assert key1 == key2


def test_schedule_lock():
    handle = locks.acquire_schedule_lock("SCH_LOCK", ttl_seconds=1)
    assert handle is not None
    second = locks.acquire_schedule_lock("SCH_LOCK", ttl_seconds=1)
    assert second is None
    handle.release()
    third = locks.acquire_schedule_lock("SCH_LOCK", ttl_seconds=1)
    assert third is not None
    third.release()
