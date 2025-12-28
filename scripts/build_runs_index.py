"""Build Runs Index - runs一覧を生成

このスクリプトは ci_run.py から呼び出され、以下を行います:
1. public/runs/*/summary.jsonを走査
2. 新しい順にソート
3. 最大50件でカット（Pages容量対策）
4. public/runs/index.jsonに出力
"""
import json
import sys
from datetime import datetime
from pathlib import Path


def load_summaries(runs_dir):
    """すべてのsummary.jsonを読み込む"""
    summaries = []
    
    if not runs_dir.exists():
        print(f"[build_runs_index] runs directory not found: {runs_dir}", file=sys.stderr)
        return summaries
    
    for run_path in runs_dir.iterdir():
        if not run_path.is_dir():
            continue
        
        summary_file = run_path / "summary.json"
        if not summary_file.exists():
            continue
        
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                summary = json.load(f)
                summaries.append(summary)
        except Exception as e:
            print(f"[build_runs_index] WARNING: Failed to load {summary_file}: {e}", file=sys.stderr)
            continue
    
    return summaries


def sort_summaries(summaries):
    """summaryを新しい順にソート"""
    def get_timestamp(summary):
        # started_at or finished_at でソート
        ts = summary.get("finished_at") or summary.get("started_at") or ""
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return datetime.min
    
    return sorted(summaries, key=get_timestamp, reverse=True)


def main():
    runs_dir = Path("public") / "runs"
    index_file = runs_dir / "index.json"
    
    # summary.jsonを読み込み
    summaries = load_summaries(runs_dir)
    print(f"[build_runs_index] Found {len(summaries)} runs")
    
    # ソート
    summaries = sort_summaries(summaries)
    
    # 最大50件でカット（Pages容量制限対策）
    MAX_RUNS = 50
    if len(summaries) > MAX_RUNS:
        print(f"[build_runs_index] Truncating to {MAX_RUNS} runs (capacity limit)")
        summaries = summaries[:MAX_RUNS]
    
    # index.jsonに出力
    runs_dir.mkdir(parents=True, exist_ok=True)
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
    
    print(f"[build_runs_index] Wrote {len(summaries)} runs to {index_file}")


if __name__ == "__main__":
    main()
