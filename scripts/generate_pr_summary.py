"""PR Summary Generator.

Per RP-179, generates PR summaries from changes.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List


def get_changed_files(base_branch: str = "main") -> List[str]:
    """Get list of changed files compared to base branch."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_branch],
            capture_output=True,
            text=True,
        )
        return [f.strip() for f in result.stdout.split("\n") if f.strip()]
    except Exception:
        return []


def categorize_changes(files: List[str]) -> dict:
    """Categorize changes by area."""
    categories = {
        "core": [],
        "tools": [],
        "tests": [],
        "docs": [],
        "scripts": [],
        "web": [],
        "config": [],
    }

    for f in files:
        if f.startswith("jarvis_core/"):
            categories["core"].append(f)
        elif f.startswith("jarvis_tools/"):
            categories["tools"].append(f)
        elif f.startswith("tests/"):
            categories["tests"].append(f)
        elif f.startswith("docs/"):
            categories["docs"].append(f)
        elif f.startswith("scripts/"):
            categories["scripts"].append(f)
        elif f.startswith("jarvis_web/"):
            categories["web"].append(f)
        else:
            categories["config"].append(f)

    return {k: v for k, v in categories.items() if v}


def generate_summary(
    base_branch: str = "main",
    include_eval_diff: bool = True,
) -> str:
    """Generate PR summary.

    Args:
        base_branch: Base branch for comparison.
        include_eval_diff: Include eval results if available.

    Returns:
        Markdown summary.
    """
    lines = ["# PR Summary", ""]

    # Changed files
    files = get_changed_files(base_branch)
    categories = categorize_changes(files)

    lines.append("## Changed Files")
    lines.append("")
    lines.append(f"Total: {len(files)} files")
    lines.append("")

    for cat, cat_files in categories.items():
        lines.append(f"### {cat.title()} ({len(cat_files)} files)")
        for f in cat_files[:5]:
            lines.append(f"- `{f}`")
        if len(cat_files) > 5:
            lines.append(f"- ... and {len(cat_files) - 5} more")
        lines.append("")

    # Test status
    lines.append("## Test Status")
    lines.append("")
    lines.append("```bash")
    lines.append("# Run to verify")
    lines.append("python -m pytest -m core -v --tb=short")
    lines.append("```")
    lines.append("")

    # Repro command
    lines.append("## Reproduction")
    lines.append("")
    lines.append("```bash")
    lines.append("git checkout <branch>")
    lines.append("pip install -r requirements.lock")
    lines.append("python -m pytest -m core")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate PR summary")
    parser.add_argument("--base", type=str, default="main")
    parser.add_argument("--output", type=str, default=None)

    args = parser.parse_args()

    summary = generate_summary(args.base)

    if args.output:
        Path(args.output).write_text(summary)
        print(f"Summary written to {args.output}")
    else:
        print(summary)


if __name__ == "__main__":
    main()
