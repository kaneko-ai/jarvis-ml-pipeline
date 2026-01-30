"""Tests for style.language_lint module."""

from pathlib import Path
import yaml

from jarvis_core.style.language_lint import LanguageLinter, LintViolation


RULES = {
    "forbidden_causal_terms": [
        {
            "pattern": "\\bproves?\\b",
            "severity": "error",
            "suggestion": "suggests",
            "explanation": "Avoid proof language.",
        },
        {
            "pattern": "確実に",
            "severity": "error",
            "suggestion": "可能性がある",
            "explanation": "断定的な表現を避ける。",
        },
    ]
}


def _write_rules(tmp_path: Path) -> Path:
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml.safe_dump(RULES, allow_unicode=True))
    return rules_file


def test_check_no_violations(tmp_path):
    rules_file = _write_rules(tmp_path)
    linter = LanguageLinter(rules_path=rules_file)

    text = "The results suggest a possible correlation."
    violations = linter.check(text)

    assert violations == []


def test_check_detects_english_pattern(tmp_path):
    rules_file = _write_rules(tmp_path)
    linter = LanguageLinter(rules_path=rules_file)

    text = "This study proves the hypothesis."
    violations = linter.check(text)

    assert any(v.pattern == "\\bproves?\\b" for v in violations)
    assert all(isinstance(v, LintViolation) for v in violations)


def test_check_detects_japanese_pattern(tmp_path):
    rules_file = _write_rules(tmp_path)
    linter = LanguageLinter(rules_path=rules_file)

    text = "この結果は確実に正しい。"
    violations = linter.check(text)

    assert any(v.pattern == "確実に" for v in violations)


def test_line_numbers(tmp_path):
    rules_file = _write_rules(tmp_path)
    linter = LanguageLinter(rules_path=rules_file)

    text = "Line one.\nLine two proves a point."
    violations = linter.check(text)

    assert violations[0].line == 2
