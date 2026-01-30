"""Tests for time.schema module."""

from jarvis_core.time.schema import (
    VariableBlock,
    TimeSchema,
    DEFAULT_TIME_SCHEMA,
)


class TestVariableBlock:
    def test_creation(self):
        block = VariableBlock(min=10, target=20, max=30)

        assert block.min == 10
        assert block.target == 20
        assert block.max == 30


class TestTimeSchema:
    def test_creation(self):
        schema = TimeSchema(
            week_hours=168,
            fixed={"sleep": 56},
            variable={"research": VariableBlock(min=30, target=45, max=60)},
        )

        assert schema.week_hours == 168

    def test_fixed_total(self):
        schema = TimeSchema(
            week_hours=168,
            fixed={"sleep": 56, "meals": 14, "commute": 10},
            variable={},
        )

        assert schema.fixed_total() == 80

    def test_variable_targets_total(self):
        schema = TimeSchema(
            week_hours=168,
            fixed={},
            variable={
                "research": VariableBlock(min=30, target=45, max=60),
                "coursework": VariableBlock(min=0, target=5, max=10),
            },
        )

        assert schema.variable_targets_total() == 50

    def test_available_variable_hours(self):
        schema = TimeSchema(
            week_hours=168,
            fixed={"sleep": 56, "meals": 14},  # 70 fixed
            variable={},
        )

        assert schema.available_variable_hours() == 98  # 168 - 70

    def test_working_hours(self):
        schema = TimeSchema(
            week_hours=168,
            fixed={},
            variable={
                "research": VariableBlock(min=30, target=45, max=60),
                "ra_ta": VariableBlock(min=0, target=10, max=20),
                "part_time": VariableBlock(min=0, target=5, max=10),
            },
        )

        assert schema.working_hours() == 60  # 45 + 10 + 5

    def test_working_hours_max(self):
        schema = TimeSchema(
            week_hours=168,
            fixed={},
            variable={
                "research": VariableBlock(min=30, target=45, max=60),
                "ra_ta": VariableBlock(min=0, target=10, max=20),
                "part_time": VariableBlock(min=0, target=5, max=10),
            },
        )

        assert schema.working_hours_max() == 90  # 60 + 20 + 10


class TestDefaultTimeSchema:
    def test_default_exists(self):
        assert DEFAULT_TIME_SCHEMA is not None
        assert DEFAULT_TIME_SCHEMA.week_hours == 168

    def test_default_has_fixed(self):
        assert "sleep" in DEFAULT_TIME_SCHEMA.fixed
        assert "meals" in DEFAULT_TIME_SCHEMA.fixed

    def test_default_has_variable(self):
        assert "research" in DEFAULT_TIME_SCHEMA.variable
        assert "rest" in DEFAULT_TIME_SCHEMA.variable
