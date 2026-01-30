from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .diff_engine import DiffReport


@dataclass
class ChangeLogResult:
    summary_lines: list[str]
    markdown: str


def generate_changelog(
    run_id: str,
    submission_version: str,
    diff_report: DiffReport,
    checklist: dict[str, object],
    attachments: list[str],
    output_path: Path,
) -> ChangeLogResult:
    summary_lines = _build_summary(diff_report, checklist)
    reason_groups = _build_reason_groups(checklist)
    impact = "Yes" if checklist.get("impact", {}).get("has_impact") else "No"
    impact_details = checklist.get("impact", {}).get("details", "")

    lines: list[str] = []
    lines.append(f"# ChangeLog ver{submission_version}")
    lines.append("")
    lines.append(f"Run ID: {run_id}")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    lines.append("## 1. 変更サマリ")
    for item in summary_lines:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## 2. 変更点（章/スライドごと）")
    if diff_report.is_empty():
        lines.append("- 初回提出または差分なし")
    else:
        _append_section_diffs(lines, "論文", diff_report.docx_sections)
        _append_section_diffs(lines, "Markdown", diff_report.md_sections)
        _append_section_diffs(lines, "スライド", diff_report.pptx_sections)
    lines.append("")

    lines.append("## 3. 変更理由")
    if not reason_groups:
        lines.append("- 先生指摘に基づく修正なし")
    else:
        for reason, items in reason_groups.items():
            lines.append(f"- {reason}: {', '.join(items)}")
    lines.append("")

    lines.append("## 4. 影響範囲")
    lines.append(f"- 結論/結果への影響: {impact}")
    if impact_details:
        lines.append(f"- 詳細: {impact_details}")
    lines.append("")

    lines.append("## 5. QA結果")
    qa = checklist.get("qa", {})
    lines.append(f"- ERROR: {qa.get('errors', 'N/A')}")
    lines.append(f"- WARN: {qa.get('warnings', 'N/A')}")
    major_warns = qa.get("major_warnings", [])
    if major_warns:
        lines.append("- 主要WARN:")
        for warn in major_warns:
            lines.append(f"  - {warn}")
    lines.append("")

    lines.append("## 6. 添付ファイル一覧")
    if attachments:
        for item in attachments:
            lines.append(f"- {item}")
    else:
        lines.append("- なし")
    lines.append("")

    lines.append("## チェック結果サマリ")
    for item in checklist.get("checks", []):
        lines.append(f"- [{item['status']}] {item['title']} ({item['id']})")

    markdown = "\n".join(lines).strip() + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    return ChangeLogResult(summary_lines=summary_lines, markdown=markdown)


def _append_section_diffs(lines: list[str], label: str, diffs: list[object]) -> None:
    if not diffs:
        return
    lines.append(f"### {label}")
    for diff in diffs:
        lines.append(f"- {diff.section}: {diff.summary}")


def _build_summary(diff_report: DiffReport, checklist: dict[str, object]) -> list[str]:
    summary = []
    changes = (
        len(diff_report.docx_sections)
        + len(diff_report.md_sections)
        + len(diff_report.pptx_sections)
    )
    if changes == 0:
        summary.append("初回提出または差分なし")
    else:
        summary.append(f"変更箇所 {changes} 件を反映")

    blocked = checklist.get("blocked", False)
    summary.append("提出チェック: OK" if not blocked else "提出チェック: NG")
    qa_errors = checklist.get("qa", {}).get("errors")
    if qa_errors is not None:
        summary.append(f"QA ERROR: {qa_errors}")

    return summary


def _build_reason_groups(checklist: dict[str, object]) -> dict[str, list[str]]:
    reasons = {}
    for item in checklist.get("checks", []):
        if item.get("status") != "pass":
            category = item.get("reason_category", "その他")
            reasons.setdefault(category, []).append(item.get("title", item.get("id", "")))
    return reasons