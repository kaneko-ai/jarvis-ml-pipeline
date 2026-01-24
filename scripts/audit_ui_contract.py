"""Audit UI contract for serverless readiness."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


HTML_PATH = Path("public/index.html")
PUBLIC_DIR = Path("public")
REPORT_PATH = Path("artifacts/ci/ui_audit.md")
STATIC_ASSETS = (
    Path("public/index.html"),
    Path("public/schedule.html"),
    Path("public/search/index.json"),
)


@dataclass(frozen=True)
class AuditIssue:
    """Represents a contract violation."""

    category: str
    message: str


@dataclass(frozen=True)
class Reference:
    """Represents a referenced path from the UI."""

    raw: str
    normalized: str
    source: str


def extract_string_literals(pattern: str, text: str) -> List[str]:
    """Extract string literals from a regex pattern with capture group."""
    return [match.group(3) for match in re.finditer(pattern, text, re.DOTALL)]


def extract_references(html: str) -> List[Reference]:
    """Extract fetch and window.location references."""
    references: List[Reference] = []
    fetch_pattern = r"(fetch\()\s*([`'\"])(.*?)\2"
    href_pattern = r"(window\.location\.href\s*=\s*)([`'\"])(.*?)\2"

    for value in extract_string_literals(fetch_pattern, html):
        normalized = normalize_path(value)
        references.append(Reference(raw=value, normalized=normalized, source="fetch"))

    for value in extract_string_literals(href_pattern, html):
        normalized = normalize_path(value)
        references.append(Reference(raw=value, normalized=normalized, source="location"))

    return references


def normalize_path(value: str) -> str:
    """Normalize a path string by stripping template expressions and query strings."""
    cleaned = re.sub(r"\$\{[^}]+\}", "", value).strip()
    if not cleaned:
        return ""
    cleaned = cleaned.split("?", 1)[0].split("#", 1)[0]
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    if cleaned.startswith("/"):
        cleaned = cleaned[1:]
    return cleaned


def should_skip_static_check(ref: Reference) -> bool:
    """Return True if reference should be excluded from static file checks."""
    raw = ref.raw.strip()
    normalized = ref.normalized
    if not normalized:
        return True
    if "${" in raw or "{{" in raw:
        return True
    if normalized.startswith("runs/") and re.search(r"(runId|\{|\$)", raw):
        return True
    if raw.startswith(("http://", "https://")) or normalized.startswith(("http://", "https://")):
        return True
    if "/api/" in raw or normalized.startswith("api/"):
        return True
    return False


def has_local_only_search_tab(html: str) -> bool:
    """Check if the search tab is marked local-only."""
    pattern = r"<[^>]+class=\"([^\"]*)\"[^>]*onclick=\"showTab\\('search'\\)\""
    for match in re.finditer(pattern, html):
        classes = match.group(1).split()
        if "local-only-tab" in classes:
            return True
    return False


def detect_search_exposure(refs: Sequence[Reference], html: str) -> Iterable[AuditIssue]:
    """Detect prohibited /api/search exposure in serverless mode."""
    uses_search = any("/api/search" in ref.raw for ref in refs)
    if not uses_search:
        return []
    if has_local_only_search_tab(html):
        return []
    return [
        AuditIssue(
            category="Serverless Exposure",
            message="API_BASE /api/search is referenced without local-only tab protection.",
        )
    ]


def check_static_files(refs: Sequence[Reference]) -> Iterable[AuditIssue]:
    """Check required static files exist under public/."""
    issues: List[AuditIssue] = []
    normalized_required = {asset.relative_to(PUBLIC_DIR).as_posix() for asset in STATIC_ASSETS}
    referenced_required = {
        ref.normalized
        for ref in refs
        if ref.normalized in normalized_required and not should_skip_static_check(ref)
    }
    assets_to_check = {PUBLIC_DIR / path for path in referenced_required}
    assets_to_check.update(STATIC_ASSETS)
    for asset in sorted(assets_to_check):
        path = asset
        if not path.exists():
            issues.append(
                AuditIssue(
                    category="Static File Missing",
                    message=f"{path} is required but missing.",
                )
            )
    return issues


def format_report(issues: Sequence[AuditIssue]) -> str:
    """Format audit report."""
    lines = ["UI Contract Audit", "=" * 40, ""]
    if not issues:
        lines.append("✓ No contract violations found.")
        return "\n".join(lines)

    lines.append("✗ Contract violations detected:")
    for issue in issues:
        lines.append(f"- [{issue.category}] {issue.message}")
    lines.append("")
    lines.append(f"Total: {len(issues)} issue(s)")
    return "\n".join(lines)


def write_report(path: Path, issues: Sequence[AuditIssue]) -> None:
    """Write audit report to docs/GAP_REPORT.md."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = format_report(issues)
    path.write_text(content, encoding="utf-8")


def run_audit(html_path: Path, write_report_flag: bool) -> int:
    """Run the audit and return exit code."""
    if not html_path.exists():
        print(f"Missing {html_path}")
        return 1

    html = html_path.read_text(encoding="utf-8")
    refs = extract_references(html)
    issues: List[AuditIssue] = []
    issues.extend(check_static_files(refs))
    issues.extend(detect_search_exposure(refs, html))

    report = format_report(issues)
    print(report)

    if write_report_flag:
        write_report(REPORT_PATH, issues)
        print(f"\nReport written to {REPORT_PATH}")

    return 1 if issues else 0


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Audit UI contract for serverless mode.")
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write audit report to artifacts/ci/ui_audit.md",
    )
    args = parser.parse_args()
    sys.exit(run_audit(HTML_PATH, args.write_report))


if __name__ == "__main__":
    main()
