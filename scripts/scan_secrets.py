"""Secrets Scanner.

Per RP-158, scans for leaked secrets in code and logs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class SecretMatch:
    """A detected secret."""

    file: str
    line: int
    pattern_name: str
    matched_text: str
    severity: str  # high, medium, low


# Secret patterns
SECRET_PATTERNS = [
    # API Keys
    (r"(?:api[_-]?key|apikey)\s*[=:]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?", "API Key", "high"),
    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI Key", "high"),
    (r"AIza[a-zA-Z0-9_\-]{35}", "Google API Key", "high"),

    # AWS
    (r"AKIA[A-Z0-9]{16}", "AWS Access Key", "high"),
    (r"(?:aws[_-]?secret|secret[_-]?key)\s*[=:]\s*['\"]?([a-zA-Z0-9/+=]{40})['\"]?", "AWS Secret", "high"),

    # Generic Secrets
    (r"(?:password|passwd|pwd)\s*[=:]\s*['\"]([^'\"]{8,})['\"]", "Password", "high"),
    (r"(?:token|auth[_-]?token)\s*[=:]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?", "Token", "medium"),

    # Private Keys
    (r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----", "Private Key", "high"),

    # Database
    (r"(?:mongo|mysql|postgres)://[^:]+:[^@]+@", "Database URL", "high"),
]


def scan_text(text: str, filename: str = "unknown") -> List[SecretMatch]:
    """Scan text for secrets.

    Args:
        text: Text to scan.
        filename: Source filename.

    Returns:
        List of SecretMatch objects.
    """
    matches = []

    lines = text.split("\n")
    for line_num, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue

        for pattern, name, severity in SECRET_PATTERNS:
            for match in re.finditer(pattern, line, re.IGNORECASE):
                matched_text = match.group(0)
                # Redact the actual secret
                if len(matched_text) > 10:
                    redacted = matched_text[:5] + "..." + matched_text[-3:]
                else:
                    redacted = matched_text[:3] + "..."

                matches.append(SecretMatch(
                    file=filename,
                    line=line_num,
                    pattern_name=name,
                    matched_text=redacted,
                    severity=severity,
                ))

    return matches


def scan_file(filepath: str) -> List[SecretMatch]:
    """Scan a file for secrets."""
    path = Path(filepath)
    if not path.exists():
        return []

    # Skip binary files
    if path.suffix in [".pyc", ".exe", ".dll", ".so", ".png", ".jpg", ".pdf"]:
        return []

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return scan_text(text, str(path))
    except Exception:
        return []


def scan_directory(directory: str, extensions: List[str] = None) -> List[SecretMatch]:
    """Scan a directory for secrets.

    Args:
        directory: Directory to scan.
        extensions: File extensions to include (default: py, json, yaml, yml, env).

    Returns:
        List of SecretMatch objects.
    """
    if extensions is None:
        extensions = [".py", ".json", ".yaml", ".yml", ".env", ".sh", ".ps1"]

    path = Path(directory)
    matches = []

    for ext in extensions:
        for file in path.rglob(f"*{ext}"):
            # Skip venv and node_modules
            if ".venv" in str(file) or "node_modules" in str(file):
                continue
            matches.extend(scan_file(str(file)))

    return matches


def format_report(matches: List[SecretMatch]) -> str:
    """Format scan results as report."""
    if not matches:
        return "✓ No secrets detected"

    lines = ["⚠️ Secrets Detected", "=" * 40, ""]

    for m in matches:
        lines.append(f"[{m.severity.upper()}] {m.pattern_name}")
        lines.append(f"  File: {m.file}:{m.line}")
        lines.append(f"  Match: {m.matched_text}")
        lines.append("")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Scan for secrets")
    parser.add_argument("--path", type=str, default=".", help="Path to scan")
    parser.add_argument("--fail-on-findings", action="store_true")

    args = parser.parse_args()

    matches = scan_directory(args.path)
    print(format_report(matches))

    if args.fail_on_findings and matches:
        sys.exit(1)


if __name__ == "__main__":
    main()
