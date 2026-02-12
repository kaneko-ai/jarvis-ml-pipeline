"""Coverage tests for jarvis_core.scheduler.engine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from jarvis_core.scheduler.engine import (
    MIN_RUN_GAP_SECONDS,
    _parse_datetime,
    _parse_rrule,
    _schedule_time,
    _tzinfo,
    due_schedules,
    is_due,
    next_run_at,
)


class TestParseDatetime:
    def test_none(self) -> None:
        assert _parse_datetime(None) is None

    def test_empty(self) -> None:
        assert _parse_datetime("") is None

    def test_valid(self) -> None:
        result = _parse_datetime("2026-01-15T10:00:00+00:00")
        assert result is not None
        assert result.year == 2026

    def test_invalid(self) -> None:
        assert _parse_datetime("not-a-date") is None


class TestParseRrule:
    def test_basic(self) -> None:
        result = _parse_rrule("FREQ=DAILY;BYHOUR=9")
        assert result["FREQ"] == "DAILY"
        assert result["BYHOUR"] == "9"

    def test_empty(self) -> None:
        result = _parse_rrule("")
        assert result == {}

    def test_no_equals(self) -> None:
        result = _parse_rrule("NOEQ;ALSO_NOEQ")
        assert result == {}


class TestScheduleTime:
    def test_defaults(self) -> None:
        t = _schedule_time({})
        assert t.hour == 0
        assert t.minute == 0

    def test_explicit(self) -> None:
        t = _schedule_time({"BYHOUR": "14", "BYMINUTE": "30", "BYSECOND": "15"})
        assert t.hour == 14
        assert t.minute == 30
        assert t.second == 15


class TestTzinfo:
    def test_utc(self) -> None:
        tz = _tzinfo({"timezone": "UTC"})
        assert tz is not None

    def test_named(self) -> None:
        tz = _tzinfo({"timezone": "Asia/Tokyo"})
        assert tz is not None

    def test_invalid(self) -> None:
        tz = _tzinfo({"timezone": "Invalid/Zone"})
        assert tz == timezone.utc

    def test_missing(self) -> None:
        tz = _tzinfo({})
        assert tz is not None


class TestNextRunAt:
    def test_no_freq(self) -> None:
        assert next_run_at({"rrule": ""}) is None

    def test_daily_future(self) -> None:
        now = datetime(2026, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        schedule = {"rrule": "FREQ=DAILY;BYHOUR=10;BYMINUTE=0"}
        result = next_run_at(schedule, now=now)
        assert result is not None
        dt = datetime.fromisoformat(result)
        assert dt.hour == 10

    def test_daily_past(self) -> None:
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        schedule = {"rrule": "FREQ=DAILY;BYHOUR=10;BYMINUTE=0"}
        result = next_run_at(schedule, now=now)
        assert result is not None
        dt = datetime.fromisoformat(result)
        assert dt.day == 16

    def test_weekly(self) -> None:
        # 2026-01-15 is Thursday
        now = datetime(2026, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        schedule = {"rrule": "FREQ=WEEKLY;BYDAY=FR;BYHOUR=9"}
        result = next_run_at(schedule, now=now)
        assert result is not None

    def test_weekly_no_match(self) -> None:
        now = datetime(2026, 1, 15, 23, 59, 59, tzinfo=timezone.utc)
        schedule = {"rrule": "FREQ=WEEKLY;BYDAY=XX;BYHOUR=9"}
        result = next_run_at(schedule, now=now)
        assert result is None

    def test_monthly(self) -> None:
        now = datetime(2026, 1, 10, 8, 0, 0, tzinfo=timezone.utc)
        schedule = {"rrule": "FREQ=MONTHLY;BYMONTHDAY=15;BYHOUR=9"}
        result = next_run_at(schedule, now=now)
        assert result is not None

    def test_monthly_past_day(self) -> None:
        now = datetime(2026, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
        schedule = {"rrule": "FREQ=MONTHLY;BYMONTHDAY=15;BYHOUR=9"}
        result = next_run_at(schedule, now=now)
        assert result is not None
        dt = datetime.fromisoformat(result)
        assert dt.month == 2

    def test_monthly_december_rollover(self) -> None:
        now = datetime(2026, 12, 20, 12, 0, 0, tzinfo=timezone.utc)
        schedule = {"rrule": "FREQ=MONTHLY;BYMONTHDAY=15;BYHOUR=9"}
        result = next_run_at(schedule, now=now)
        assert result is not None
        dt = datetime.fromisoformat(result)
        assert dt.year == 2027
        assert dt.month == 1

    def test_unknown_freq(self) -> None:
        assert next_run_at({"rrule": "FREQ=YEARLY"}) is None

    def test_with_timezone(self) -> None:
        now = datetime(2026, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        schedule = {"rrule": "FREQ=DAILY;BYHOUR=10", "timezone": "Asia/Tokyo"}
        result = next_run_at(schedule, now=now)
        assert result is not None


class TestIsDue:
    def test_disabled(self) -> None:
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert is_due({"enabled": False, "rrule": "FREQ=DAILY;BYHOUR=10"}, now, None) is False

    def test_degraded(self) -> None:
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert is_due({"degraded": True, "rrule": "FREQ=DAILY;BYHOUR=10"}, now, None) is False

    def test_no_freq(self) -> None:
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert is_due({"rrule": ""}, now, None) is False

    def test_daily_due(self) -> None:
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert is_due({"rrule": "FREQ=DAILY;BYHOUR=10"}, now, None) is True

    def test_daily_already_ran(self) -> None:
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        last = "2026-01-15T11:00:00+00:00"
        assert is_due({"rrule": "FREQ=DAILY;BYHOUR=10"}, now, last) is False

    def test_daily_before_time(self) -> None:
        now = datetime(2026, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        assert is_due({"rrule": "FREQ=DAILY;BYHOUR=10"}, now, None) is True

    def test_weekly_due(self) -> None:
        # Thursday
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert is_due({"rrule": "FREQ=WEEKLY;BYDAY=TH;BYHOUR=10"}, now, None) is True

    def test_monthly_due(self) -> None:
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert is_due({"rrule": "FREQ=MONTHLY;BYMONTHDAY=15;BYHOUR=10"}, now, None) is True

    def test_monthly_before_day(self) -> None:
        now = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
        schedule = {"rrule": "FREQ=MONTHLY;BYMONTHDAY=15;BYHOUR=10"}
        result = is_due(schedule, now, None)
        # Before scheduled day, last occurrence is previous month => due unless already run.
        assert result is True

    def test_monthly_january_rollback(self) -> None:
        now = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
        schedule = {"rrule": "FREQ=MONTHLY;BYMONTHDAY=15;BYHOUR=10"}
        assert is_due(schedule, now, None) is True

    def test_gap_too_small(self) -> None:
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        last_run = (now - timedelta(seconds=30)).isoformat()
        assert is_due({"rrule": "FREQ=DAILY;BYHOUR=10"}, now, last_run) is False

    def test_unknown_freq_in_is_due(self) -> None:
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert is_due({"rrule": "FREQ=YEARLY"}, now, None) is False


class TestDueSchedules:
    def test_empty(self) -> None:
        assert due_schedules([]) == []

    def test_some_due(self) -> None:
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        schedules = [
            {"rrule": "FREQ=DAILY;BYHOUR=10", "name": "daily"},
            {"enabled": False, "rrule": "FREQ=DAILY;BYHOUR=10", "name": "disabled"},
        ]
        result = due_schedules(schedules, now=now)
        assert len(result) == 1
        assert result[0]["name"] == "daily"
