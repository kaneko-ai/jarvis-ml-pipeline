"""Runbook generation from lessons learned."""

from __future__ import annotations

import re
from pathlib import Path


def generate_runbook(
    *,
    lessons_path: Path = Path("knowledge/failures/lessons_learned.md"),
    output_path: Path = Path("reports/runbook.md"),
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = lessons_path.read_text(encoding="utf-8", errors="ignore") if lessons_path.exists() else ""
    categories = re.findall(r"^- category:\s*(.+)\s*$", text, flags=re.MULTILINE)
    causes = re.findall(r"^- root_cause:\s*(.+)\s*$", text, flags=re.MULTILINE)
    checks = re.findall(r"^- block_rule:\s*(.+)\s*$", text, flags=re.MULTILINE)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Ops+Extract Runbook\n\n")
        if not categories:
            f.write("- No lessons data available.\n")
            return output_path
        f.write("## Frequent Categories\n")
        for idx, category in enumerate(categories[:20], start=1):
            f.write(f"{idx}. {category}\n")
        f.write("\n## Root Causes\n")
        for idx, cause in enumerate(causes[:20], start=1):
            f.write(f"{idx}. {cause}\n")
        f.write("\n## Preventive Checks\n")
        for idx, check in enumerate(checks[:20], start=1):
            f.write(f"{idx}. {check}\n")
    return output_path

