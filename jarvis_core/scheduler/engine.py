"""Schedule engine for due computation."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

MIN_RUN_GAP_SECONDS = 60


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_rrule(rrule_text: str) -> dict[str, str]:
    parts = {}
    for chunk in rrule_text.split(";"):
        if "=" in chunk:
            key, value = chunk.split("=", 1)
            parts[key.upper()] = value
    return parts


def _schedule_time(parts: dict[str, str]) -> time:
    hour = int(parts.get("BYHOUR", 0))
    minute = int(parts.get("BYMINUTE", 0))
    second = int(parts.get("BYSECOND", 0))
    return time(hour=hour, minute=minute, second=second)


def _tzinfo(schedule: dict[str, Any]) -> timezone:
    tz_name = schedule.get("timezone", "UTC")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return timezone.utc


def next_run_at(schedule: dict[str, Any], now: datetime | None = None) -> str | None:
    now = now or datetime.now(timezone.utc)
    parts = _parse_rrule(schedule.get("rrule", ""))
    freq = parts.get("FREQ")
    if not freq:
        return None
    tzinfo = _tzinfo(schedule)
    localized = now.astimezone(tzinfo)
    scheduled_time = _schedule_time(parts)
    if freq == "DAILY":
        candidate = localized.replace(
            hour=scheduled_time.hour,
            minute=scheduled_time.minute,
            second=scheduled_time.second,
            microsecond=0,
        )
        if candidate <= localized:
            candidate = candidate + timedelta(days=1)
        return candidate.astimezone(timezone.utc).isoformat()
    if freq == "WEEKLY":
        byday = parts.get("BYDAY", "MO").split(",")
        weekdays = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
        allowed = {weekdays.index(day) for day in byday if day in weekdays}
        for offset in range(0, 8):
            candidate_date = localized.date() + timedelta(days=offset)
            if candidate_date.weekday() not in allowed:
                continue
            candidate = datetime.combine(candidate_date, scheduled_time, tzinfo=tzinfo)
            if candidate > localized:
                return candidate.astimezone(timezone.utc).isoformat()
        return None
    if freq == "MONTHLY":
        day = int(parts.get("BYMONTHDAY", 1))
        candidate = localized.replace(
            day=day,
            hour=scheduled_time.hour,
            minute=scheduled_time.minute,
            second=scheduled_time.second,
            microsecond=0,
        )
        if candidate <= localized:
            month = candidate.month + 1
            year = candidate.year + (1 if month > 12 else 0)
            month = 1 if month > 12 else month
            candidate = candidate.replace(year=year, month=month, day=day)
        return candidate.astimezone(timezone.utc).isoformat()
    return None


def is_due(schedule: dict[str, Any], now: datetime, last_run_at: str | None) -> bool:
    if not schedule.get("enabled", True):
        return False
    if schedule.get("degraded"):
        return False
    parts = _parse_rrule(schedule.get("rrule", ""))
    freq = parts.get("FREQ")
    if not freq:
        return False
    tzinfo = _tzinfo(schedule)
    localized = now.astimezone(tzinfo)
    scheduled_time = _schedule_time(parts)
    last_occurrence = None
    if freq == "DAILY":
        candidate = localized.replace(
            hour=scheduled_time.hour,
            minute=scheduled_time.minute,
            second=scheduled_time.second,
            microsecond=0,
        )
        if candidate > localized:
            candidate = candidate - timedelta(days=1)
        last_occurrence = candidate
    elif freq == "WEEKLY":
        byday = parts.get("BYDAY", "MO").split(",")
        weekdays = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
        allowed = {weekdays.index(day) for day in byday if day in weekdays}
        for offset in range(0, 8):
            candidate_date = localized.date() - timedelta(days=offset)
            if candidate_date.weekday() not in allowed:
                continue
            candidate = datetime.combine(candidate_date, scheduled_time, tzinfo=tzinfo)
            if candidate <= localized:
                last_occurrence = candidate
                break
    elif freq == "MONTHLY":
        day = int(parts.get("BYMONTHDAY", 1))
        candidate = localized.replace(
            day=day,
            hour=scheduled_time.hour,
            minute=scheduled_time.minute,
            second=scheduled_time.second,
            microsecond=0,
        )
        if candidate > localized:
            month = candidate.month - 1
            year = candidate.year - (1 if month < 1 else 0)
            month = 12 if month < 1 else month
            candidate = candidate.replace(year=year, month=month, day=day)
        last_occurrence = candidate
    if not last_occurrence:
        return False
    last_run_dt = _parse_datetime(last_run_at)
    if last_run_dt and last_run_dt >= last_occurrence:
        return False
    if last_run_dt:
        if (now - last_run_dt).total_seconds() < MIN_RUN_GAP_SECONDS:
            return False
    return True


def due_schedules(
    schedules: list[dict[str, Any]], now: datetime | None = None
) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    due: list[dict[str, Any]] = []
    for schedule in schedules:
        if is_due(schedule, now, schedule.get("last_run_at")):
            due.append(schedule)
    return due