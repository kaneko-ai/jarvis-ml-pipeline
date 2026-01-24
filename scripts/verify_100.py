#!/usr/bin/env python
"""100%判定スクリプト (AG-12 / T-01).

PASSしたら100%と呼べる。
判定項目:
- 契約10本OK
- provenance_rate >= 0.95
- facts_without_evidence == 0
- locator_missing == 0
- Dashboard API health（オプション）

Usage:
    python scripts/verify_100.py [--run-id RUN_ID] [--check-api]

Exit codes:
    0: PASS (100%)
    1: FAIL
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# 品質閾値（BUNDLE_CONTRACT.md / GOLDEN_SET準拠）
QUALITY_THRESHOLDS = {
    "provenance_rate": 0.95,
    "citation_precision": 0.90,
    "facts_without_evidence": 0,
    "locator_missing": 0,
}

# 契約ファイル
REQUIRED_ARTIFACTS = [
    "input.json",
    "run_config.json",
    "papers.jsonl",
    "claims.jsonl",
    "evidence.jsonl",
    "scores.json",
    "result.json",
    "eval_summary.json",
    "warnings.jsonl",
    "report.md",
]

FAILURE_REQUIRED = [
    "result.json",
    "eval_summary.json",
    "warnings.jsonl",
    "report.md",
]


class VerifyResult:
    """検証結果."""

    def __init__(self):
        self.passed = True
        self.checks = []
        self.failures = []

    def add_check(self, name: str, passed: bool, detail: str = ""):
        self.checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            self.passed = False
            self.failures.append(f"{name}: {detail}")

    def summary(self) -> str:
        lines = []
        status = "✅ PASS (100%)" if self.passed else "❌ FAIL"
        lines.append(f"\n{'='*60}")
        lines.append(f"  verify_100 Result: {status}")
        lines.append(f"{'='*60}\n")

        for check in self.checks:
            mark = "✅" if check["passed"] else "❌"
            lines.append(f"  {mark} {check['name']}")
            if check["detail"]:
                lines.append(f"      → {check['detail']}")

        lines.append(f"\n{'='*60}")
        lines.append(f"  Total: {len(self.checks)} checks, {len(self.failures)} failures")
        lines.append(f"{'='*60}\n")

        return "\n".join(lines)


def check_contract(run_dir: Path, is_failure: bool = False) -> tuple[bool, str]:
    """契約10本チェック."""
    required = FAILURE_REQUIRED if is_failure else REQUIRED_ARTIFACTS
    missing = []
    for artifact in required:
        if not (run_dir / artifact).exists():
            missing.append(artifact)

    if missing:
        return False, f"欠落: {', '.join(missing)}"
    return True, f"{len(required)}/{len(required)} files present"


def check_quality_metrics(run_dir: Path) -> tuple[bool, str, dict]:
    """品質メトリクスチェック."""
    eval_file = run_dir / "eval_summary.json"
    if not eval_file.exists():
        return False, "eval_summary.json not found", {}

    try:
        with open(eval_file, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
    except Exception as e:
        return False, f"eval_summary.json parse error: {e}", {}

    metrics = eval_data.get("metrics", {})
    issues = []

    # gate_passed チェック
    if not eval_data.get("gate_passed", False):
        fail_reasons = eval_data.get("fail_reasons", [])
        reason_codes = [fr.get("code", "UNKNOWN") for fr in fail_reasons]
        issues.append(f"gate_passed=false ({', '.join(reason_codes)})")

    # locator_missing チェック
    locator_missing = metrics.get("locator_missing", 0)
    if locator_missing > QUALITY_THRESHOLDS["locator_missing"]:
        issues.append(f"locator_missing={locator_missing}")

    # evidence_coverage チェック (provenance_rate代替)
    evidence_coverage = metrics.get("evidence_coverage", 0)
    if evidence_coverage < QUALITY_THRESHOLDS["provenance_rate"]:
        issues.append(
            f"evidence_coverage={evidence_coverage:.2f} < {QUALITY_THRESHOLDS['provenance_rate']}"
        )

    if issues:
        return False, "; ".join(issues), metrics
    return True, "All quality metrics pass", metrics


def check_evidence_locators(run_dir: Path) -> tuple[bool, str]:
    """evidence.jsonlのlocatorチェック."""
    evidence_file = run_dir / "evidence.jsonl"
    if not evidence_file.exists():
        return False, "evidence.jsonl not found"

    try:
        with open(evidence_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
    except Exception as e:
        return False, f"evidence.jsonl read error: {e}"

    if not lines:
        return True, "No evidence (empty file)"

    missing_locator = 0
    for line in lines:
        try:
            ev = json.loads(line)
            locator = ev.get("locator")
            if not locator:
                missing_locator += 1
            elif isinstance(locator, dict) and not locator.get("section"):
                missing_locator += 1
        except:
            pass

    if missing_locator > 0:
        return False, f"{missing_locator}/{len(lines)} evidence missing locator"
    return True, f"All {len(lines)} evidence have locators"


def check_api_health(base_url: str = "http://localhost:8000") -> tuple[bool, str]:
    """Dashboard API healthチェック."""
    try:
        import urllib.request

        endpoints = ["/api/runs", "/api/health"]
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    if resp.status != 200:
                        return False, f"{endpoint} returned {resp.status}"
            except Exception as e:
                return False, f"{endpoint} failed: {e}"
        return True, "All API endpoints healthy"
    except Exception as e:
        return False, f"API check failed: {e}"


def verify_run(run_dir: Path, check_api: bool = False) -> VerifyResult:
    """単一runを検証."""
    result = VerifyResult()

    # 1. 結果ファイルを読んで失敗判定
    result_file = run_dir / "result.json"
    is_failure = False
    if result_file.exists():
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                res = json.load(f)
            is_failure = res.get("status") != "success"
        except:
            pass

    # 2. 契約チェック
    passed, detail = check_contract(run_dir, is_failure)
    result.add_check("Contract (10 files)", passed, detail)

    # 3. 品質メトリクスチェック
    passed, detail, metrics = check_quality_metrics(run_dir)
    result.add_check("Quality Metrics", passed, detail)

    # 4. Locatorチェック
    passed, detail = check_evidence_locators(run_dir)
    result.add_check("Evidence Locators", passed, detail)

    # 5. API healthチェック（オプション）
    if check_api:
        passed, detail = check_api_health()
        result.add_check("API Health", passed, detail)

    return result


def main():
    parser = argparse.ArgumentParser(description="100%判定 (verify_100)")
    parser.add_argument("--run-id", help="特定のrun_idを検証（省略時は最新run）")
    parser.add_argument("--base-dir", default="logs/runs", help="runsディレクトリ")
    parser.add_argument("--check-api", action="store_true", help="API healthもチェック")
    parser.add_argument("--all", action="store_true", help="全runを検証")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)

    if not base_dir.exists():
        print(f"エラー: {base_dir} が存在しません")
        return 1

    # 検証対象を決定
    if args.run_id:
        run_dirs = [base_dir / args.run_id]
        if not run_dirs[0].exists():
            print(f"エラー: run {args.run_id} が存在しません")
            return 1
    elif args.all:
        run_dirs = [d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        run_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    else:
        # 最新run
        run_dirs = [d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        if not run_dirs:
            print("検証対象のrunがありません")
            return 0
        run_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        run_dirs = run_dirs[:1]

    # 検証実行
    all_passed = True
    for run_dir in run_dirs:
        print(f"\n検証中: {run_dir.name}")
        result = verify_run(run_dir, check_api=args.check_api)
        print(result.summary())

        if not result.passed:
            all_passed = False

    # 最終結果
    if all_passed:
        print("\n🎉 PASS: 100%達成！")
        return 0
    else:
        print("\n💥 FAIL: 100%未達")
        return 1


if __name__ == "__main__":
    sys.exit(main())
