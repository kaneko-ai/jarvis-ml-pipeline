"""Tests for time.calendar_builder module."""

from jarvis_core.time.calendar_builder import build_months, build_weeks


class TestCalendarBuilder:
    def test_build_months_basic(self):
        """Test basic month building."""
        months = build_months("2024-01", 3)
        assert months == ["2024-01", "2024-02", "2024-03"]

    def test_build_months_year_wrap(self):
        """Test month building across year boundary."""
        months = build_months("2024-11", 4)
        assert months == ["2024-11", "2024-12", "2025-01", "2025-02"]

    def test_build_months_single(self):
        """Test single month."""
        months = build_months("2024-06", 1)
        assert months == ["2024-06"]

    def test_build_weeks_basic(self):
        """Test basic week building."""
        weeks = build_weeks("2024-01-01", 3)
        assert len(weeks) == 3
        assert weeks[0] == "2024-01-01"
        assert weeks[1] == "2024-01-08"
        assert weeks[2] == "2024-01-15"

    def test_build_weeks_single(self):
        """Test single week."""
        weeks = build_weeks("2024-06-15", 1)
        assert weeks == ["2024-06-15"]

    def test_build_weeks_month_wrap(self):
        """Test week building across month boundary."""
        weeks = build_weeks("2024-01-29", 2)
        assert weeks[0] == "2024-01-29"
        assert weeks[1] == "2024-02-05"