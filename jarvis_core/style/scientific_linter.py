"""Scientific linter for P6 lint signals."""

from __future__ import annotations

from typing import Any

from jarvis_core.reporting.language_lint import LanguageLinter

AMBIGUOUS_TERMS = ["some", "many", "various", "significant", "可能性", "様々"]
WEAK_EVIDENCE_TERMS = ["probably", "maybe", "おそらく", "推測", "仮説"]


class ScientificLinter:
    """Lightweight linting for scientific drafts."""

    def __init__(self):
        self.language_linter = LanguageLinter()

    def lint_text(self, text: str) -> list[dict[str, Any]]:
        violations = []
        violations.extend(self.language_linter.lint_text(text))

        for term in AMBIGUOUS_TERMS:
            if term.lower() in text.lower():
                violations.append(
                    {
                        "code": "AMBIGUOUS_TERM",
                        "severity": "warning",
                        "term": term,
                        "message": f"Ambiguous term detected: {term}",
                    }
                )

        for term in WEAK_EVIDENCE_TERMS:
            if term.lower() in text.lower():
                violations.append(
                    {
                        "code": "WEAK_EVIDENCE",
                        "severity": "warning",
                        "term": term,
                        "message": f"Weak evidence language detected: {term}",
                    }
                )

        return violations

    def lint_features(self, text: str) -> dict[str, int]:
        violations = self.lint_text(text)
        return {
            "error_count": sum(1 for v in violations if v["severity"] == "error"),
            "warn_count": sum(1 for v in violations if v["severity"] == "warning"),
        }
