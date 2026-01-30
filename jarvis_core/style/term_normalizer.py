"""Term normalization utilities for lab style guide."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

STYLE_GUIDE_PATH = Path(__file__).with_name("lab_style_guide.yaml")


@dataclass
class TermIssue:
    issue_type: str
    location: str
    original: str
    suggested: str
    rule_id: str
    severity: str


@dataclass
class NormalizationResult:
    normalized_lines: list[str]
    issues: list[TermIssue]
    replacements: list[dict[str, str]]


def load_style_guide(path: Path = STYLE_GUIDE_PATH) -> dict[str, object]:
    """Load the lab style guide YAML."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _apply_variants(
    line: str,
    variants: list[str],
    preferred: str,
    rule_id: str,
    location: str,
    issue_type: str,
    severity: str,
) -> tuple[str, list[TermIssue], list[dict[str, str]]]:
    issues: list[TermIssue] = []
    replacements: list[dict[str, str]] = []

    def _replace(match: re.Match) -> str:
        original = match.group(0)
        if original == preferred:
            return original
        issues.append(
            TermIssue(
                issue_type=issue_type,
                location=location,
                original=original,
                suggested=preferred,
                rule_id=rule_id,
                severity=severity,
            )
        )
        replacements.append(
            {
                "location": location,
                "original": original,
                "suggested": preferred,
                "rule_id": rule_id,
            }
        )
        return preferred

    for pattern in variants:
        line = re.sub(pattern, _replace, line, flags=re.IGNORECASE)

    return line, issues, replacements


def normalize_lines(
    lines: list[str],
    style_guide: dict[str, object],
    source_prefix: str,
) -> NormalizationResult:
    """Normalize lines according to style guide."""
    normalized_lines: list[str] = []
    issues: list[TermIssue] = []
    replacements: list[dict[str, str]] = []

    preferred_terms = style_guide.get("preferred_terms", [])
    forbidden_terms = style_guide.get("forbidden_terms", [])
    unit_variants = style_guide.get("units_and_notation", {}).get("unit_variants", [])

    for idx, line in enumerate(lines, start=1):
        location = f"{source_prefix}:{idx}"
        updated = line
        for entry in preferred_terms:
            updated, entry_issues, entry_replacements = _apply_variants(
                updated,
                entry.get("variants", []),
                entry.get("preferred", ""),
                entry.get("id", "preferred_term"),
                location,
                "term_variant",
                "WARN",
            )
            issues.extend(entry_issues)
            replacements.extend(entry_replacements)
        for entry in unit_variants:
            updated, entry_issues, entry_replacements = _apply_variants(
                updated,
                entry.get("variants", []),
                entry.get("preferred", ""),
                entry.get("id", "unit_variant"),
                location,
                "unit_format",
                "WARN",
            )
            issues.extend(entry_issues)
            replacements.extend(entry_replacements)
        for entry in forbidden_terms:
            pattern = entry.get("pattern", "")
            if not pattern:
                continue
            for match in re.finditer(pattern, updated):
                original = match.group(0)
                issues.append(
                    TermIssue(
                        issue_type="forbidden_term",
                        location=location,
                        original=original,
                        suggested="(remove or replace)",
                        rule_id=entry.get("id", "forbidden_term"),
                        severity="ERROR",
                    )
                )
        normalized_lines.append(updated)

    return NormalizationResult(
        normalized_lines=normalized_lines,
        issues=issues,
        replacements=replacements,
    )


def check_abbrev_rules(
    text: str, style_guide: dict[str, object], source_prefix: str
) -> list[TermIssue]:
    issues: list[TermIssue] = []
    abbrev_rules = style_guide.get("abbrev_rules", [])
    lines = text.splitlines()
    for rule in abbrev_rules:
        abbreviation = rule.get("abbreviation")
        full_form = rule.get("full_form")
        if not abbreviation or not full_form:
            continue
        abbreviation_pattern = re.compile(rf"\b{re.escape(abbreviation)}\b")
        full_pattern = re.compile(re.escape(full_form), re.IGNORECASE)
        if not abbreviation_pattern.search(text):
            continue
        first_abbrev_line = None
        for idx, line in enumerate(lines, start=1):
            if abbreviation_pattern.search(line):
                first_abbrev_line = idx
                break
        if first_abbrev_line is None:
            continue
        text_before = "\n".join(lines[:first_abbrev_line])
        if not full_pattern.search(text_before):
            issues.append(
                TermIssue(
                    issue_type="abbrev_missing",
                    location=f"{source_prefix}:{first_abbrev_line}",
                    original=abbreviation,
                    suggested=rule.get("first_use_format", f"{full_form} ({abbreviation})"),
                    rule_id=rule.get("id", "abbrev_rule"),
                    severity="WARN",
                )
            )
    return issues


def normalize_markdown(
    text: str, style_guide: dict[str, object]
) -> tuple[str, list[TermIssue], list[dict[str, str]]]:
    lines = text.splitlines()
    result = normalize_lines(lines, style_guide, source_prefix="md")
    issues = result.issues + check_abbrev_rules(text, style_guide, "md")
    return "\n".join(result.normalized_lines), issues, result.replacements


def normalize_docx_paragraphs(
    paragraphs: list[str], style_guide: dict[str, object]
) -> NormalizationResult:
    return normalize_lines(paragraphs, style_guide, source_prefix="docx")


def normalize_pptx_slides(slides: list[str], style_guide: dict[str, object]) -> NormalizationResult:
    return normalize_lines(slides, style_guide, source_prefix="pptx")