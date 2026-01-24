#!/usr/bin/env python
"""Bundle契約監査スクリプト (AG-01).

Bundle契約（10ファイル必須）の遵守状況を監査し、
報告書を生成する。

Usage:
    python scripts/audit_bundle.py [--run-id RUN_ID]

Output:
    reports/audit_bundle_status.md
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


# 契約定義（BUNDLE_CONTRACT.md準拠）
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

# 各ファイルの必須キー
REQUIRED_KEYS = {
    "input.json": ["goal", "query", "constraints"],
    "run_config.json": ["run_id", "pipeline", "timestamp"],
    "papers.jsonl": ["paper_id", "title", "year"],
    "claims.jsonl": ["claim_id", "paper_id", "claim_text"],
    "evidence.jsonl": ["claim_id", "paper_id", "evidence_text", "locator"],
    "scores.json": ["features", "rankings"],
    "result.json": ["run_id", "status", "answer", "citations"],
    "eval_summary.json": ["gate_passed", "fail_reasons", "metrics"],
    "warnings.jsonl": ["code", "message", "severity"],
}


def check_json_keys(filepath: Path, required_keys: list[str]) -> list[str]:
    """JSONファイルの必須キーをチェック."""
    missing_keys = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in required_keys:
            if key not in data:
                missing_keys.append(key)
    except Exception as e:
        missing_keys.append(f"[読み込みエラー: {e}]")
    return missing_keys


def check_jsonl_keys(filepath: Path, required_keys: list[str]) -> list[str]:
    """JSONLファイルの必須キーをチェック（最初の行のみ）."""
    missing_keys = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if not first_line:
                return ["[ファイルが空]"]
            data = json.loads(first_line)
            for key in required_keys:
                if key not in data:
                    missing_keys.append(key)
    except Exception as e:
        missing_keys.append(f"[読み込みエラー: {e}]")
    return missing_keys


def audit_run(run_dir: Path) -> dict[str, Any]:
    """単一runを監査."""
    result = {
        "run_id": run_dir.name,
        "run_dir": str(run_dir),
        "files": {},
        "missing_files": [],
        "missing_keys": {},
        "contract_valid": True,
    }

    for artifact in REQUIRED_ARTIFACTS:
        filepath = run_dir / artifact
        if not filepath.exists():
            result["files"][artifact] = {"exists": False}
            result["missing_files"].append(artifact)
            result["contract_valid"] = False
        else:
            result["files"][artifact] = {
                "exists": True,
                "size": filepath.stat().st_size,
            }

            # キーチェック
            if artifact in REQUIRED_KEYS:
                if artifact.endswith(".jsonl"):
                    missing = check_jsonl_keys(filepath, REQUIRED_KEYS[artifact])
                else:
                    missing = check_json_keys(filepath, REQUIRED_KEYS[artifact])

                if missing:
                    result["missing_keys"][artifact] = missing
                    result["contract_valid"] = False

    return result


def generate_report(audits: list[dict[str, Any]], output_path: Path) -> None:
    """監査報告書を生成."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    valid_count = sum(1 for a in audits if a["contract_valid"])
    total_count = len(audits)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Bundle契約監査報告書\n\n")
        f.write(f"生成日時: {datetime.now().isoformat()}\n\n")
        f.write("---\n\n")

        # サマリ
        f.write("## サマリ\n\n")
        f.write(f"- 監査対象run数: {total_count}\n")
        f.write(f"- 契約遵守run数: {valid_count}\n")
        f.write(f"- 契約違反run数: {total_count - valid_count}\n")
        f.write(
            f"- 遵守率: {valid_count/total_count*100:.1f}%\n"
            if total_count > 0
            else "- 遵守率: N/A\n"
        )
        f.write("\n---\n\n")

        # 契約定義
        f.write("## 契約定義（BUNDLE_CONTRACT.md）\n\n")
        f.write("必須10ファイル:\n")
        for artifact in REQUIRED_ARTIFACTS:
            f.write(f"- `{artifact}`\n")
        f.write("\n---\n\n")

        # 詳細
        f.write("## 監査詳細\n\n")
        for audit in audits:
            status = "✅ 遵守" if audit["contract_valid"] else "❌ 違反"
            f.write(f"### {audit['run_id']} - {status}\n\n")

            if audit["missing_files"]:
                f.write("**欠落ファイル:**\n")
                for mf in audit["missing_files"]:
                    f.write(f"- `{mf}`\n")
                f.write("\n")

            if audit["missing_keys"]:
                f.write("**欠落キー:**\n")
                for file, keys in audit["missing_keys"].items():
                    f.write(f"- `{file}`: {', '.join(keys)}\n")
                f.write("\n")

            if audit["contract_valid"]:
                f.write("すべての契約を満たしています。\n\n")

        # DoD
        f.write("---\n\n")
        f.write("## DoD確認\n\n")
        f.write("- [x] 監査スクリプト実行完了\n")
        f.write(f"- {'[x]' if valid_count == total_count else '[ ]'} 全runが契約遵守\n")
        f.write("- [x] 報告書生成完了\n")


def main():
    parser = argparse.ArgumentParser(description="Bundle契約監査")
    parser.add_argument("--run-id", help="特定のrun_idを監査（省略時は全run）")
    parser.add_argument("--base-dir", default="logs/runs", help="runsディレクトリ")
    parser.add_argument("--output", default="reports/audit_bundle_status.md", help="出力ファイル")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)

    if not base_dir.exists():
        print(f"エラー: {base_dir} が存在しません")
        return 1

    # 監査対象を決定
    if args.run_id:
        run_dirs = [base_dir / args.run_id]
        if not run_dirs[0].exists():
            print(f"エラー: run {args.run_id} が存在しません")
            return 1
    else:
        run_dirs = [d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]

    if not run_dirs:
        print("監査対象のrunがありません")
        return 0

    # 監査実行
    print(f"監査開始: {len(run_dirs)} runs")
    audits = []
    for run_dir in sorted(run_dirs, key=lambda p: p.stat().st_mtime, reverse=True):
        print(f"  監査中: {run_dir.name}")
        audits.append(audit_run(run_dir))

    # 報告書生成
    output_path = Path(args.output)
    generate_report(audits, output_path)
    print(f"\n報告書生成: {output_path}")

    # 結果サマリ
    valid_count = sum(1 for a in audits if a["contract_valid"])
    if valid_count == len(audits):
        print(f"✅ 全{len(audits)}runが契約遵守")
        return 0
    else:
        print(f"❌ {len(audits) - valid_count}/{len(audits)}runが契約違反")
        return 1


if __name__ == "__main__":
    exit(main())
