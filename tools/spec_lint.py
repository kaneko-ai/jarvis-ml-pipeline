#!/usr/bin/env python3
"""
JARVIS Spec Lint

仕様文書の権威レベルと強制語彙の整合性をチェック。
REFERENCE/ROADMAP文書で強制語彙が使われていたらfail。

Usage:
    python tools/spec_lint.py
    python tools/spec_lint.py --fix  # 将来用（自動修正）
"""

import argparse
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
AUTHORITY_PATTERN = re.compile(
    r">\s*Authority:\s*(\w+)\s*\(Level\s*(\d+),\s*(Binding|Non-binding)\)"
)

# NonBindingレベル（強制語彙禁止）
NON_BINDING_LEVELS = {"REFERENCE", "ROADMAP"}

# 例外ファイル（強制語彙を許可 / Authorityヘッダー不要）
EXCEPTIONS = {
    "SPEC_AUTHORITY.md",  # 権威定義文書自体
    "DECISIONS.md",  # 決定記録
    "coverage_daily.md",  # 自動更新ログ
    "DAILY_COVERAGE_TASKS.md",  # 実装タスク一覧
    "index.md",
    "browser.md",
    "mcp.md",
    "mcp_config.md",
    "multi_agent.md",
    "rules.md",
    "skills.md",
    "terminal_security.md",
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
        print(f"[ERROR] Failed to read {filepath}: {e}")
        return violations

    authority = extract_authority(content)

    # Authorityがない場合はエラー
    if authority is None:
        violations.append(
            Violation(
                file=str(filepath),
                line=1,
                word="MISSING_AUTHORITY_HEADER",
                authority="NONE",
            )
        )
        return violations

    # Binding文書は強制語彙OK
    if authority not in NON_BINDING_LEVELS:
        return violations

    # Non-binding文書で強制語彙をチェック
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        # Authority Header自体はスキップ
        if i <= 3 and "Authority:" in line:
            continue

        for pattern in FORCE_PATTERNS:
            match = pattern.search(line)
            if match:
                violations.append(
                    Violation(
                        file=str(filepath),
                        line=i,
                        word=match.group(),
                        authority=authority,
                    )
                )

    return violations


def main() -> int:
    """メイン."""
    parser = argparse.ArgumentParser(description="JARVIS Spec Lint")
    parser.add_argument("--paths", nargs="+", help="Check specific files")
    args = parser.parse_args()

    docs_dir = Path(__file__).parent.parent / "docs"

    if args.paths:
        files = [Path(p) for p in args.paths]
    else:
        if not docs_dir.exists():
            print(f"[ERROR] docs directory not found: {docs_dir}")
            return 1
        files = list(docs_dir.glob("**/*.md"))

    all_violations: List[Violation] = []
    checked = 0

    for md_file in files:
        if not md_file.exists():
            print(f"[WARN] File not found: {md_file}")
            continue
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
