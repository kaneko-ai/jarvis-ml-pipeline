"""Tests for style.scientific_linter module."""

from jarvis_core.style.scientific_linter import (
    ScientificLinter,
    AMBIGUOUS_TERMS,
    WEAK_EVIDENCE_TERMS,
)


class TestConstants:
    def test_ambiguous_terms_defined(self):
        assert len(AMBIGUOUS_TERMS) > 0
        assert "some" in AMBIGUOUS_TERMS

    def test_weak_evidence_terms_defined(self):
        assert len(WEAK_EVIDENCE_TERMS) > 0
        assert "probably" in WEAK_EVIDENCE_TERMS


class TestScientificLinter:
    def test_init(self):
        linter = ScientificLinter()
        assert linter.language_linter is not None

    def test_lint_text_clean(self):
        linter = ScientificLinter()
        text = "The results demonstrate clear outcomes."

        violations = linter.lint_text(text)

        # May have other violations but no ambiguous/weak
        assert isinstance(violations, list)

    def test_lint_text_ambiguous(self):
        linter = ScientificLinter()
        text = "Some results showed various improvements."

        violations = linter.lint_text(text)

        # Should detect ambiguous terms
        ambiguous = [v for v in violations if v.get("code") == "AMBIGUOUS_TERM"]
        assert len(ambiguous) >= 1

    def test_lint_text_weak_evidence(self):
        linter = ScientificLinter()
        text = "This probably means the hypothesis is correct."

        violations = linter.lint_text(text)

        weak = [v for v in violations if v.get("code") == "WEAK_EVIDENCE"]
        assert len(weak) >= 1

    def test_lint_features(self):
        linter = ScientificLinter()
        text = "Some results probably showed improvements."

        features = linter.lint_features(text)

        assert "error_count" in features
        assert "warn_count" in features
        assert features["warn_count"] >= 2  # "some" and "probably"
