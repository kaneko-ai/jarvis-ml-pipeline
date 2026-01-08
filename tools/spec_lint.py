#!/usr/bin/env python3
"""
JARVIS Spec Lint

仕様文書の権威レベルと強制語彙の整合性をチェック。
REFERENCE/ROADMAP文書で強制語彙が使われていたらfail。

Usage:
    python tools/spec_lint.py
    python tools/spec_lint.py --fix  # 将来用（自動修正）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional


class Violation(NamedTuple):
    """違反."""
    file: str
    line: int
    word: str
    authority: str


# 強制語彙（REFERENCE/ROADMAPで禁止）
FORCE_WORDS_EN = [
    r"\bMUST\b",
    r"\bSHALL\b",
    r"\bREQUIRED\b",
    r"\bNEVER\b",
    r"\bALWAYS\b",
]

FORCE_WORDS_JA = [
    r"必須",
    r"厳守",
    r"しなければならない",
    r"してはいけない",
    r"禁止",
    r"常に",
    r"絶対に",
]

FORCE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in FORCE_WORDS_EN + FORCE_WORDS_JA]

# Authority Header パターン
AUTHORITY_PATTERN = re.compile(r">\s*Authority:\s*(\w+)\s*\(Level\s*(\d+),\s*(Binding|Non-binding)\)")

# NonBindingレベル（強制語彙禁止）
NON_BINDING_LEVELS = {"REFERENCE", "ROADMAP"}

# 例外ファイル（強制語彙を許可）
EXCEPTIONS = {
    "SPEC_AUTHORITY.md",  # 権威定義文書自体
    "DECISIONS.md",  # 決定記録
}


def extract_authority(content: str) -> Optional[str]:
    """Authority Headerから分類を抽出."""
    match = AUTHORITY_PATTERN.search(content)
    if match:
        return match.group(1).upper()
    return None


def check_file(filepath: Path) -> List[Violation]:
    """ファイルをチェック."""
    violations = []

    # 例外チェック
    if filepath.name in EXCEPTIONS:
        return violations

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"DEBUG: Failed to read {filepath}: {e}")
        return violations

    authority = extract_authority(content)
    print(f"DEBUG: Checking {filepath}, Authority: {authority}")

    # Authorityがない場合はスキップ（警告のみ）
    if authority is None:
        print(f"[WARN] No Authority Header: {filepath}")
        return violations

    # Binding文書は強制語彙OK
    if authority not in NON_BINDING_LEVELS:
        return violations

    # Non-binding文書で強制語彙をチェック
    lines = content.split("\n")
    print(f"DEBUG: Checking {len(lines)} lines")
    for i, line in enumerate(lines, 1):
        # Authority Header自体はスキップ
        if i <= 3 and "Authority:" in line:
            print(f"DEBUG: Skipping header line {i}: {line}")
            continue

        print(f"DEBUG: Line {i}: '{line}'")
        for pattern in FORCE_PATTERNS:
            match = pattern.search(line)
            if match:
                print(f"DEBUG: Match found: {match.group()} in '{line}'")
                print(f"DEBUG: Size before append: {len(violations)}")
                violations.append(Violation(
                    file=str(filepath),
                    line=i,
                    word=match.group(),
                    authority=authority,
                ))
                print(f"DEBUG: Size after append: {len(violations)}")

    return violations


def main() -> int:
    """メイン."""
    docs_dir = Path(__file__).parent.parent / "docs"

    if not docs_dir.exists():
        print(f"[ERROR] docs directory not found: {docs_dir}")
        return 1

    all_violations: List[Violation] = []
    checked = 0

    for md_file in docs_dir.glob("**/*.md"):
        violations = check_file(md_file)
        all_violations.extend(violations)
        checked += 1

    print(f"Checked {checked} files")

    if all_violations:
        print(f"\n[FAIL] {len(all_violations)} violations found:\n")
        for v in all_violations:
            print(f"  {v.file}:{v.line} [{v.authority}] '{v.word}'")
        return 1

    print("[PASS] No violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
