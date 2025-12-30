"""Build Runs Index - runs一覧を生成

このスクリプトは ci_run.py から呼び出され、以下を行います:
1. public/runs/*/manifest.jsonを走査
2. 新しい順にソート
3. 最大50件でカット（Pages容量対策）
4. public/runs/index.jsonに出力
"""
import json
import sys
from datetime import datetime
from pathlib import Path


def load_manifests(runs_dir):
    """すべてのmanifest.jsonを読み込む"""
    manifests = []
    
    if not runs_dir.exists():
        print(f"[build_runs_index] runs directory not found: {runs_dir}", file=sys.stderr)
        return manifests
    
    for run_path in runs_dir.iterdir():
        if not run_path.is_dir():
            continue
        
        manifest_file = run_path / "manifest.json"
        if not manifest_file.exists():
            continue
        
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                manifests.append(manifest)
        except Exception as e:
            print(f"[build_runs_index] WARNING: Failed to load {manifest_file}: {e}", file=sys.stderr)
            continue
    
    return manifests


def sort_manifests(manifests):
    """manifestを新しい順にソート"""
    def get_timestamp(manifest):
        ts = manifest.get("created_at") or ""
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return datetime.min
    
    return sorted(manifests, key=get_timestamp, reverse=True)


def extract_index_entry(manifest):
    """manifestからindex用の最小情報を抽出"""
    quality = manifest.get("quality", {})
    return {
        "run_id": manifest.get("run_id"),
        "status": manifest.get("status"),
        "created_at": manifest.get("created_at"),
        "papers_found": quality.get("papers_found"),
        "gate_passed": quality.get("gate_passed"),
    }


def main():
    runs_dir = Path("public") / "runs"
    index_file = runs_dir / "index.json"
    
    # manifest.jsonを読み込み
    manifests = load_manifests(runs_dir)
    print(f"[build_runs_index] Found {len(manifests)} runs")
    
    # ソート
    manifests = sort_manifests(manifests)
    
    # 最大50件でカット（Pages容量制限対策）
    MAX_RUNS = 50
    if len(manifests) > MAX_RUNS:
        print(f"[build_runs_index] Truncating to {MAX_RUNS} runs (capacity limit)")
        manifests = manifests[:MAX_RUNS]

    index_entries = [extract_index_entry(manifest) for manifest in manifests]
    
    # index.jsonに出力
    runs_dir.mkdir(parents=True, exist_ok=True)
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_entries, f, indent=2, ensure_ascii=False)
    
    print(f"[build_runs_index] Wrote {len(index_entries)} runs to {index_file}")


if __name__ == "__main__":
    main()
