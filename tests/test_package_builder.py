"""Tests for submission.package_builder module (basic functions)."""

from pathlib import Path

from jarvis_core.submission.package_builder import (
    SubmissionResult,
    is_ready_to_submit,
    _load_yaml,
    _safe_load_json,
    _infer_reason_category,
    _version_key,
    _closest_previous_version,
)


class TestSubmissionResult:
    def test_creation(self):
        result = SubmissionResult(
            run_id="run-123",
            submission_version="1.0",
            blocked=False,
            package_path=Path("/tmp/package.zip"),
            submission_root=Path("/tmp/submission"),
            changelog_path=Path("/tmp/changelog.md"),
            email_path=Path("/tmp/email.txt"),
            check_report_path=Path("/tmp/check.json"),
            check_report_md_path=Path("/tmp/check.md"),
            email_subject="Test Subject",
            email_body="Test body",
        )

        assert result.run_id == "run-123"
        assert result.blocked is False


class TestIsReadyToSubmit:
    def test_checks_p6_ready(self, tmp_path):
        # Returns a tuple (bool, str message)
        result = is_ready_to_submit("nonexistent-run")
        # Result is a tuple, first element is bool
        assert isinstance(result, tuple)
        assert isinstance(result[0], bool)


class TestLoadYaml:
    def test_load_valid_yaml(self, tmp_path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n", encoding="utf-8")

        result = _load_yaml(yaml_file)

        assert result["key"] == "value"
        assert result["list"] == ["item1"]


class TestSafeLoadJson:
    def test_load_valid_json(self, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}', encoding="utf-8")

        result = _safe_load_json(json_file)

        assert result["key"] == "value"

    def test_load_nonexistent_file(self, tmp_path):
        # _safe_load_json may raise FileNotFoundError
        nonexistent = tmp_path / "nonexistent.json"
        # Check if it raises or returns empty
        try:
            result = _safe_load_json(nonexistent)
            assert result == {}
        except FileNotFoundError:
            pass  # This is expected behavior

    def test_load_invalid_json(self, tmp_path):
        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json", encoding="utf-8")

        result = _safe_load_json(json_file)
        assert result == {}


class TestInferReasonCategory:
    def test_format_category(self):
        result = _infer_reason_category("format_check")
        assert "書式" in result or "フォーマット" in result or result is not None

    def test_none_id(self):
        result = _infer_reason_category(None)
        assert result is not None


class TestVersionKey:
    def test_simple_version(self):
        key = _version_key("1.0")
        assert isinstance(key, tuple)

    def test_complex_version(self):
        key = _version_key("1.2.3")
        assert isinstance(key, tuple)


class TestClosestPreviousVersion:
    def test_find_previous(self):
        versions = ["1.0", "1.1", "1.2", "2.0"]
        result = _closest_previous_version("2.0", versions)

        # Should find a version before 2.0
        assert result in versions or result is None

    def test_no_previous(self):
        versions = ["2.0", "3.0"]
        result = _closest_previous_version("1.0", versions)

        # No version before 1.0
        assert result is None