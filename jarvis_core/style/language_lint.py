"""Language linting for causal claim detection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


@dataclass
class LintViolation:
    """Language lint violation."""

    line: int
    pattern: str
    severity: str
    suggestion: str


class LanguageLinter:
    """Checks text against forbidden causal language rules."""

    def __init__(self, rules_path: Path | None = None) -> None:
        if rules_path is None:
            rules_path = Path(__file__).parent.parent.parent / "docs" / "LANGUAGE_RULES.yaml"
        self.rules = self._load_rules(rules_path)

    @staticmethod
    def _load_rules(path: Path) -> dict[str, Any]:
        raw = path.read_bytes()
        text = None
        for encoding in ("utf-8", "utf-8-sig", "cp932", "cp1252", "latin-1"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            return {}
        return yaml.safe_load(text) or {}

    def check(self, text: str) -> list[LintViolation]:
        """Check text for violations.

        Args:
            text: Input text.

        Returns:
            List of LintViolation entries.
        """
        violations: list[LintViolation] = []
        rules = self.rules.get("forbidden_causal_terms", [])

        for line_number, line in enumerate(text.splitlines(), start=1):
            for rule in rules:
                pattern = rule.get("pattern")
                if not pattern:
                    continue
                if re.search(pattern, line, flags=re.IGNORECASE):
                    violations.append(
                        LintViolation(
                            line=line_number,
                            pattern=pattern,
                            severity=rule.get("severity", "warning"),
                            suggestion=rule.get("suggestion", ""),
                        )
                    )

        return violations
