# Daily Coverage Snapshot 実装タスク一覧

Codexで段階的に実装を進めるためのタスク定義。
「Task 1-3を実行して」のように指示する。

---

## 概要

Daily Coverage Snapshotシステムを実装するための10個のタスク。
各タスクは独立して実行可能で、前のタスクの成果物に依存する場合は明記している。

---

## Task 1: coverage_daily.md テンプレート作成

### 目的
カバレッジ履歴を蓄積するMDファイルを作成する。

### 作成ファイル
`docs/coverage_daily.md`

### 内容
# Daily Coverage Snapshot

<!-- This file is auto-updated. Do not edit manually. -->
<!-- Timezone: Asia/Tokyo (JST) -->

---

## 運用ルール

1. このファイルは自動更新される（手動編集禁止）
2. 数値を盛る目的の除外は`COVERAGE_POLICY.md`で禁止されている

---

## Log

<!-- newest entries are appended at the end -->

### 検証
- ファイルが存在すること
- Markdownとして正しくレンダリングされること

---

## Task 2: daily_coverage_snapshot.sh 基本構造

### 目的
カバレッジ測定スクリプトの基本構造を作成する。

### 作成ファイル
`scripts/daily_coverage_snapshot.sh`

### 仕様
```bash
#!/usr/bin/env bash
# Daily Coverage Snapshot (non-gating)
# Purpose: 測定のみ行い、fail_underでブロックしない
# Usage: COVERAGE_PHASE=1 bash scripts/daily_coverage_snapshot.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

PHASE="${COVERAGE_PHASE:-1}"
ARTIFACTS_DIR="${ARTIFACTS_DIR:-artifacts}"

# Phase validation
if [[ "$PHASE" != "1" && "$PHASE" != "2" ]]; then
    echo "ERROR: Invalid COVERAGE_PHASE=$PHASE (use 1 or 2)" >&2
    exit 2
fi

# Config selection
if [[ "$PHASE" == "1" ]]; then
    CFG=".coveragerc.phase1"
else
    CFG=".coveragerc.phase2"
fi

# Config existence check
if [[ ! -f "$CFG" ]]; then
    echo "ERROR: Config file not found: $CFG" >&2
    exit 1
fi

echo "=== Daily Coverage Snapshot ==="
echo "Date: $(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S JST')"
echo "Phase: $PHASE"
echo "Config: $CFG"
echo "==============================="
```

### 検証
- `bash scripts/daily_coverage_snapshot.sh` が設定情報を出力すること
- 不正なPHASEでexit 2になること

---

## Task 3: daily_coverage_snapshot.sh pytest実行部分

### 目的
Task 2で作成したスクリプトにpytest実行部分を追加する。

### 依存
Task 2

### 追加内容
Task 2のスクリプト末尾に以下を追加:

```bash
# Prepare artifacts directory
mkdir -p "$ARTIFACTS_DIR"

# Clean up existing coverage files
rm -f .coverage .coverage.* 2>/dev/null || true

# Run pytest with coverage (ignore test failures for snapshot)
echo ""
echo "Running tests with coverage..."
set +e
python -m pytest \
    --cov=jarvis_core \
    --cov-config="$CFG" \
    --cov-report=xml \
    --cov-report=html \
    --cov-report=term-missing \
    -q \
    2>&1 | tee "$ARTIFACTS_DIR/pytest_output.txt"
PYTEST_EXIT=$?
set -e

echo ""
echo "Pytest exit code: $PYTEST_EXIT (ignored for snapshot)"
```

### 検証
- `bash scripts/daily_coverage_snapshot.sh` でpytestが実行されること
- `artifacts/pytest_output.txt` が生成されること

---

## Task 4: daily_coverage_snapshot.sh レポート生成部分

### 目的
Task 3で作成したスクリプトにカバレッジレポート生成部分を追加する。

### 依存
Task 3

### 追加内容
Task 3のスクリプト末尾に以下を追加:

```bash
# Combine parallel coverage files if any
if ls .coverage.* 1>/dev/null 2>&1; then
    echo "Combining coverage data..."
    python -m coverage combine --rcfile="$CFG" 2>/dev/null || true
fi

echo ""
echo "=== Coverage Report (non-gating) ==="

# Create temporary config without fail_under
TEMP_CFG=$(mktemp)
grep -v "^fail_under" "$CFG" > "$TEMP_CFG" || cp "$CFG" "$TEMP_CFG"

# Generate report
python -m coverage report --rcfile="$TEMP_CFG" 2>&1 | tee "$ARTIFACTS_DIR/coverage_daily_term.txt"

# Cleanup temp config
rm -f "$TEMP_CFG"

# Move artifacts
mv coverage.xml "$ARTIFACTS_DIR/" 2>/dev/null || true
mv htmlcov "$ARTIFACTS_DIR/" 2>/dev/null || true

echo ""
echo "=== Snapshot Complete ==="
echo "Artifacts saved to: $ARTIFACTS_DIR/"

# Always exit 0 (this is snapshot, not gate)
exit 0
```

### 検証
- `bash scripts/daily_coverage_snapshot.sh` が正常終了すること
- `artifacts/coverage_daily_term.txt` が生成されること
- `artifacts/coverage.xml` が生成されること

---

## Task 5: append_coverage_daily_md.py 基本構造

### 目的
MD追記スクリプトの基本構造を作成する。

### 作成ファイル
`scripts/append_coverage_daily_md.py`

### 内容
```python
#!/usr/bin/env python3
"""
Append daily coverage snapshot to docs/coverage_daily.md

Usage:
    python scripts/append_coverage_daily_md.py \\
        --md docs/coverage_daily.md \\
        --report artifacts/coverage_daily_term.txt

Environment Variables:
    COVERAGE_PHASE: 1 or 2 (default: 1)
    GITHUB_SHA: commit SHA (from GitHub Actions)
    GITHUB_REPOSITORY: owner/repo (from GitHub Actions)
    GITHUB_RUN_ID: workflow run ID (from GitHub Actions)
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore


TOTAL_RE = re.compile(r"^TOTAL\s+\d+\s+\d+\s+(\d+)%\s*$", re.MULTILINE)
TOTAL_RE_BRANCH = re.compile(r"^TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Snapshot:
    """Immutable snapshot data."""
    date_jst: str
    phase: str
    total_pct: str
    commit_sha: str
    run_url: str
    notes: str = ""


if __name__ == "__main__":
    print("Script structure OK")
```

### 検証
- `python scripts/append_coverage_daily_md.py` が "Script structure OK" を出力すること

---

## Task 6: append_coverage_daily_md.py パース関数

### 目的
Task 5で作成したスクリプトにパース関数を追加する。

### 依存
Task 5

### 追加内容
Snapshotクラスの後に以下を追加:

```python
def parse_total_percent(report_text: str) -> str:
    """Extract total coverage percentage from report output."""
    match = TOTAL_RE.search(report_text)
    if match:
        return f"{match.group(1)}%"
    
    match = TOTAL_RE_BRANCH.search(report_text)
    if match:
        return f"{match.group(1)}%"
    
    for line in report_text.splitlines():
        if line.strip().startswith("TOTAL"):
            parts = line.split()
            for part in reversed(parts):
                if part.endswith("%"):
                    return part
    
    raise ValueError(
        "Could not find TOTAL coverage percent in report output.\n"
        f"Report content:\n{report_text[:500]}"
    )


def get_previous_coverage(md_path: Path) -> Optional[str]:
    """Get the most recent coverage value from the MD file."""
    if not md_path.exists():
        return None
    
    content = md_path.read_text(encoding="utf-8")
    matches = re.findall(r"total_coverage:\s*(\d+%)", content)
    return matches[-1] if matches else None


def calculate_delta(current: str, previous: Optional[str]) -> str:
    """Calculate coverage delta string."""
    if not previous:
        return ""
    
    try:
        curr_val = int(current.rstrip("%"))
        prev_val = int(previous.rstrip("%"))
        delta = curr_val - prev_val
        if delta > 0:
            return f" (+{delta}%)"
        elif delta < 0:
            return f" ({delta}%)"
        else:
            return " (±0%)"
    except ValueError:
        return ""
```

### 検証
- スクリプトがimportエラーなく読み込めること

---

## Task 7: append_coverage_daily_md.py ファイル操作関数

### 目的
Task 6で作成したスクリプトにファイル操作関数を追加する。

### 依存
Task 6

### 追加内容
calculate_delta関数の後に以下を追加:

```python
def ensure_header(md_path: Path) -> None:
    """Ensure the MD file exists with proper header."""
    if md_path.exists():
        content = md_path.read_text(encoding="utf-8").strip()
        if content and "# Daily Coverage Snapshot" in content:
            return
    
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        "# Daily Coverage Snapshot\n\n"
        "> **Authority**: REFERENCE (Level 4, Non-binding)  \n"
        "> **Purpose**: 毎日1回のカバレッジ計測結果を時系列で蓄積する  \n"
        "> **Timezone**: Asia/Tokyo（JST）\n\n"
        "---\n\n"
        "## Log\n\n"
        "<!-- newest entries are appended at the end -->\n"
        "<!-- DO NOT EDIT MANUALLY -->\n",
        encoding="utf-8",
    )


def append_entry(md_path: Path, snap: Snapshot, delta: str) -> None:
    """Append a new entry to the MD file."""
    entry_lines = [
        f"\n### {snap.date_jst}",
        f"- phase: {snap.phase}",
        f"- total_coverage: {snap.total_pct}{delta}",
        f"- commit: `{snap.commit_sha}`",
    ]
    
    if snap.run_url:
        entry_lines.append(f"- workflow_run: {snap.run_url}")
    
    if snap.notes:
        entry_lines.append(f"- notes: {snap.notes}")
    
    entry_lines.append("")
    
    entry = "\n".join(entry_lines)
    
    current_content = md_path.read_text(encoding="utf-8")
    md_path.write_text(current_content + entry, encoding="utf-8")
```

### 検証
- スクリプトがimportエラーなく読み込めること

---

## Task 8: append_coverage_daily_md.py main関数

### 目的
Task 7で作成したスクリプトにmain関数を追加する。

### 依存
Task 7

### 追加内容
append_entry関数の後、`if __name__ == "__main__":` の前に以下を追加:

```python
def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Append daily coverage snapshot to MD file"
    )
    parser.add_argument(
        "--md",
        default="docs/coverage_daily.md",
        help="Path to coverage_daily.md",
    )
    parser.add_argument(
        "--report",
        default="artifacts/coverage_daily_term.txt",
        help="Path to coverage report text file",
    )
    parser.add_argument(
        "--phase",
        default=os.environ.get("COVERAGE_PHASE", "1"),
        help="Coverage phase (1 or 2)",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional notes to include",
    )
    args = parser.parse_args()

    md_path = Path(args.md)
    report_path = Path(args.report)

    if not report_path.exists():
        print(f"ERROR: Report file not found: {report_path}", file=sys.stderr)
        return 1

    ensure_header(md_path)

    try:
        report_text = report_path.read_text(encoding="utf-8")
        total_pct = parse_total_percent(report_text)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    jst = ZoneInfo("Asia/Tokyo")
    date_jst = datetime.now(tz=jst).strftime("%Y-%m-%d")

    commit_sha = os.environ.get("GITHUB_SHA", "")[:12] or "local"
    
    run_url = ""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if repo and run_id:
        run_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    previous_coverage = get_previous_coverage(md_path)
    delta = calculate_delta(total_pct, previous_coverage)

    snap = Snapshot(
        date_jst=date_jst,
        phase=str(args.phase),
        total_pct=total_pct,
        commit_sha=commit_sha,
        run_url=run_url,
        notes=args.notes,
    )
    
    append_entry(md_path, snap, delta)
    
    print(f"Appended coverage snapshot: {date_jst} - {total_pct}{delta}")
    return 0
```

また、`if __name__ == "__main__":` ブロックを以下に変更:

```python
if __name__ == "__main__":
    sys.exit(main())
```

### 検証
- `python scripts/append_coverage_daily_md.py --help` が正常に表示されること

---

## Task 9: GitHub Actions Workflow作成

### 目的
毎日自動でカバレッジを測定するGitHub Actions Workflowを作成する。

### 作成ファイル
`.github/workflows/coverage-daily.yml`

### 内容
```yaml
name: Daily Coverage Snapshot

on:
  schedule:
    - cron: "10 15 * * *"
  workflow_dispatch:
    inputs:
      phase:
        description: "Coverage phase (1 or 2)"
        required: false
        default: "1"
      notes:
        description: "Optional notes for this snapshot"
        required: false
        default: ""

permissions:
  contents: write

concurrency:
  group: coverage-daily
  cancel-in-progress: false

env:
  PYTHON_VERSION: "3.11"
  ARTIFACTS_DIR: "artifacts"

jobs:
  snapshot:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: |
          uv sync --dev
          uv pip install coverage[toml]

      - name: Prepare artifacts directory
        run: mkdir -p ${{ env.ARTIFACTS_DIR }}

      - name: Run daily coverage snapshot
        env:
          COVERAGE_PHASE: ${{ github.event.inputs.phase || '1' }}
          ARTIFACTS_DIR: ${{ env.ARTIFACTS_DIR }}
        run: |
          chmod +x scripts/daily_coverage_snapshot.sh
          bash scripts/daily_coverage_snapshot.sh

      - name: Append result to docs/coverage_daily.md
        env:
          COVERAGE_PHASE: ${{ github.event.inputs.phase || '1' }}
        run: |
          python scripts/append_coverage_daily_md.py \
            --md docs/coverage_daily.md \
            --report ${{ env.ARTIFACTS_DIR }}/coverage_daily_term.txt \
            --phase "$COVERAGE_PHASE" \
            --notes "${{ github.event.inputs.notes || '' }}"

      - name: Check for changes
        id: check_changes
        run: |
          if git diff --quiet docs/coverage_daily.md; then
            echo "changed=false" >> $GITHUB_OUTPUT
          else
            echo "changed=true" >> $GITHUB_OUTPUT
          fi

      - name: Commit and push
        if: steps.check_changes.outputs.changed == 'true'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/coverage_daily.md
          git commit -m "chore(coverage): daily snapshot $(TZ=Asia/Tokyo date '+%Y-%m-%d') [skip ci]"
          for i in 1 2 3; do
            git pull --rebase origin main && git push && break
            echo "Push failed, retrying ($i/3)..."
            sleep 5
          done

      - name: Upload coverage artifacts
        uses: actions/upload-artifact@v4
        with:
          name: coverage-daily-${{ github.run_id }}
          path: |
            ${{ env.ARTIFACTS_DIR }}/coverage_daily_term.txt
            ${{ env.ARTIFACTS_DIR }}/coverage.xml
            ${{ env.ARTIFACTS_DIR }}/htmlcov/
          retention-days: 30
          if-no-files-found: warn

      - name: Summary
        run: |
          echo "## Daily Coverage Snapshot" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "Date: $(TZ=Asia/Tokyo date '+%Y-%m-%d')" >> $GITHUB_STEP_SUMMARY
          echo "Phase: ${{ github.event.inputs.phase || '1' }}" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### Coverage Report" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          tail -20 ${{ env.ARTIFACTS_DIR }}/coverage_daily_term.txt >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
```

### 検証
- YAMLの構文が正しいこと
- インデントがスペース2つで統一されていること

---

## Task 10: COVERAGE_POLICY.md更新

### 目的
既存のCOVERAGE_POLICY.mdにDaily Snapshotとの役割分担セクションを追記する。

### 更新ファイル
`docs/COVERAGE_POLICY.md`

### 追記内容
ファイル末尾に以下を追加:

```markdown

---

## Daily Coverage Snapshotとの役割分担

### 目的の違い

| 観点 | CIゲート（本ポリシー） | Daily Snapshot |
|------|------------------------|----------------|
| 目的 | PRの品質担保 | 継続的な観測・トレンド把握 |
| 実行タイミング | PR/push時 | 毎日00:10 JST |
| fail_under | 有効（85%/95%） | 無効 |
| 失敗時 | CIブロック | ログ記録のみ |

### 参照ドキュメント

- 詳細仕様: `docs/JAVIS_STATE_AND_ROADMAP.md` セクション8
- 実装: `scripts/daily_coverage_snapshot.sh`, `scripts/append_coverage_daily_md.py`
- 履歴: `docs/coverage_daily.md`

### 禁止事項（共通）

Daily Snapshotの数値が低いからといって、以下を行ってはならない:

1. `# pragma: no cover`を追加してカバレッジを上げる
2. `.coveragerc`の除外パターンを拡大する
3. テストをスキップする

これらはCIゲートのポリシー違反として扱われる。
```

### 検証
- Markdownとして正しくレンダリングされること
- 既存の内容が変更されていないこと

- 「docs/DAILY_COVERAGE_TASKS.md を参照して Task 5-8 を実行して」
- 「docs/DAILY_COVERAGE_TASKS.md を参照して Task 9-10 を実行して」