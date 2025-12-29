"""Figure/Table registry for placeholder and reference validation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import re


@dataclass
class FigureEntry:
    fig_id: str
    placeholder_exists: bool
    referenced_in_text: bool


@dataclass
class RegistryIssue:
    issue_type: str
    message: str
    fig_id: str


def scan_text(text: str) -> Dict[str, List[Dict[str, object]]]:
    placeholder_pattern = re.compile(r"\[\[FIGURE_PLACEHOLDER:(FIG\d+)\]\]")
    table_pattern = re.compile(r"\[\[TABLE_PLACEHOLDER:(TABLE\d+)\]\]")
    ref_pattern = re.compile(r"\b(Fig\.?|Figure)\s*(\d+)")
    table_ref_pattern = re.compile(r"\b(Table)\s*(\d+)")

    placeholders = placeholder_pattern.findall(text)
    table_placeholders = table_pattern.findall(text)
    refs = [f"FIG{num}" for _, num in ref_pattern.findall(text)]
    table_refs = [f"TABLE{num}" for _, num in table_ref_pattern.findall(text)]

    figures: List[FigureEntry] = []
    issues: List[RegistryIssue] = []

    seen = set()
    for fig_id in placeholders:
        if fig_id in seen:
            issues.append(
                RegistryIssue(
                    issue_type="duplicate_id",
                    message="重複する図番号が検出されました",
                    fig_id=fig_id,
                )
            )
            continue
        seen.add(fig_id)
        figures.append(
            FigureEntry(
                fig_id=fig_id,
                placeholder_exists=True,
                referenced_in_text=fig_id in refs,
            )
        )

    for fig in figures:
        if not fig.referenced_in_text:
            issues.append(
                RegistryIssue(
                    issue_type="missing_reference",
                    message="本文内参照が見つかりません",
                    fig_id=fig.fig_id,
                )
            )

    figure_numbers = [int(fig.fig_id.replace("FIG", "")) for fig in figures]
    if figure_numbers:
        expected = list(range(min(figure_numbers), min(figure_numbers) + len(figure_numbers)))
        if sorted(figure_numbers) != expected:
            issues.append(
                RegistryIssue(
                    issue_type="non_sequential_number",
                    message="図番号が連番になっていません",
                    fig_id=",".join([fig.fig_id for fig in figures]),
                )
            )

    table_entries: List[FigureEntry] = []
    table_seen = set()
    for table_id in table_placeholders:
        if table_id in table_seen:
            issues.append(
                RegistryIssue(
                    issue_type="duplicate_id",
                    message="重複する表番号が検出されました",
                    fig_id=table_id,
                )
            )
            continue
        table_seen.add(table_id)
        table_entries.append(
            FigureEntry(
                fig_id=table_id,
                placeholder_exists=True,
                referenced_in_text=table_id in table_refs,
            )
        )

    for table in table_entries:
        if not table.referenced_in_text:
            issues.append(
                RegistryIssue(
                    issue_type="missing_reference",
                    message="本文内参照が見つかりません",
                    fig_id=table.fig_id,
                )
            )

    table_numbers = [int(t.fig_id.replace("TABLE", "")) for t in table_entries]
    if table_numbers:
        expected = list(range(min(table_numbers), min(table_numbers) + len(table_numbers)))
        if sorted(table_numbers) != expected:
            issues.append(
                RegistryIssue(
                    issue_type="non_sequential_number",
                    message="表番号が連番になっていません",
                    fig_id=",".join([t.fig_id for t in table_entries]),
                )
            )

    return {
        "figures": [f.__dict__ for f in figures],
        "tables": [t.__dict__ for t in table_entries],
        "issues": [i.__dict__ for i in issues],
    }
