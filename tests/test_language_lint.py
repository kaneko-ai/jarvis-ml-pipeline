"""Tests for reporting.language_lint module."""

from unittest.mock import patch
import pytest

from jarvis_core.reporting.language_lint import (
    LanguageLinter,
    lint_report_fail_on_error,
)


@pytest.fixture
def mock_rules():
    """Mock language rules."""
    return {
        "forbidden": ["cause", "prove", "confirm"],
        "forbidden_ja": ["確実に", "必ず"],
        "conditional_required": ["may", "might", "possibly"],
        "conditional_required_ja": ["可能性がある", "かもしれない"],
    }


class TestLanguageLinter:
    def test_init(self, tmp_path, mock_rules):
        # Create a temporary rules file
        import yaml

        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml.dump(mock_rules))

        linter = LanguageLinter(rules_path=rules_file)

        assert linter.rules is not None

    def test_lint_text_clean(self, tmp_path, mock_rules):
        import yaml

        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml.dump(mock_rules))
        linter = LanguageLinter(rules_path=rules_file)

        text = "The results suggest a possible correlation."

        violations = linter.lint_text(text)

        # No forbidden terms
        errors = [v for v in violations if v["severity"] == "error"]
        assert len(errors) == 0

    def test_lint_text_forbidden_english(self, tmp_path, mock_rules):
        import yaml

        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml.dump(mock_rules))
        linter = LanguageLinter(rules_path=rules_file)

        text = "This study proves that the hypothesis is correct."

        violations = linter.lint_text(text)

        errors = [v for v in violations if v["term"] == "prove"]
        assert len(errors) >= 1

    def test_lint_text_forbidden_japanese(self, tmp_path, mock_rules):
        import yaml

        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml.dump(mock_rules))
        linter = LanguageLinter(rules_path=rules_file)

        text = "この結果は確実に正しい。"

        violations = linter.lint_text(text)

        errors = [v for v in violations if "確実" in v.get("term", "")]
        assert len(errors) >= 1

    def test_check_hedging_required_with_hedging(self, tmp_path, mock_rules):
        import yaml

        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml.dump(mock_rules))
        linter = LanguageLinter(rules_path=rules_file)

        text = "This may indicate a correlation."

        violations = linter.check_hedging_required(text, "要注意")

        # Has hedging ("may"), so no violation
        assert len(violations) == 0

    def test_check_hedging_required_without_hedging(self, tmp_path, mock_rules):
        import yaml

        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml.dump(mock_rules))
        linter = LanguageLinter(rules_path=rules_file)

        text = "This indicates a correlation."

        violations = linter.check_hedging_required(text, "推測")

        # Missing hedging for uncertain content
        warnings = [v for v in violations if v["code"] == "HEDGING_REQUIRED"]
        assert len(warnings) >= 1

    def test_check_hedging_not_required_for_certain(self, tmp_path, mock_rules):
        import yaml

        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml.dump(mock_rules))
        linter = LanguageLinter(rules_path=rules_file)

        text = "This is a definite statement."

        # Certainty level doesn't require hedging
        violations = linter.check_hedging_required(text, "確定")

        assert len(violations) == 0

    def test_lint_report(self, tmp_path, mock_rules):
        import yaml

        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml.dump(mock_rules))
        linter = LanguageLinter(rules_path=rules_file)

        report_file = tmp_path / "report.md"
        report_file.write_text("# Report\n\nThis study proves nothing.")

        violations = linter.lint_report(report_file)

        assert isinstance(violations, list)


class TestLintReportFailOnError:
    def test_passes_clean_report(self, tmp_path):
        import yaml

        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(
            yaml.dump(
                {
                    "forbidden": [],
                    "forbidden_ja": [],
                }
            )
        )

        report_file = tmp_path / "report.md"
        report_file.write_text("# Clean Report\n\nContent here.")

        with patch("jarvis_core.reporting.language_lint.Path") as mock_path:
            # Mock the default rules path to use our temp file
            with patch.object(
                LanguageLinter,
                "__init__",
                lambda self, rules_path=None: setattr(
                    self, "rules", {"forbidden": [], "forbidden_ja": []}
                ),
            ):
                # Create fresh linter
                result = lint_report_fail_on_error(report_file)

                assert result is True
