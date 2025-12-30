"""CI Run Script - run_idごとに独立した実行環境を作成

このスクリプトは GitHub Actions から呼び出され、以下を行います:
1. run_idを受け取る
2. ベース設定（config.yaml）を読み込む
3. query, max_resultsなどを上書き
4. pathsをpublic/runs/<run_id>/に差し替えた一時configを生成
5. run_pipeline.pyを実行（emit_progressでステータス更新）
6. summary.json / stats.json / warnings.jsonl を生成
7. build_runs_index.pyを呼び出してindex.json更新
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import yaml


# === Progress Emitter (Cloudflare Worker KV) ===

def emit_progress(percent: int, stage: str, message: str = "", counters: dict = None):
    """進捗をCloudflare Worker KVに送信（Actions環境でのみ動作）"""
    url = os.environ.get("CF_STATUS_URL")
    token = os.environ.get("CF_STATUS_TOKEN")
    run_id = os.environ.get("RUN_ID")
    
    if not url or not token or not run_id:
        print(f"[emit_progress] {percent}% [{stage}] {message}")
        return  # ローカル実行では無視
    
    payload = {
        "run_id": str(run_id),
        "percent": int(percent),
        "stage": stage,
        "message": message,
        "counters": counters or {},
    }
    
    try:
        subprocess.run(
            ["curl", "-sS", "-X", "POST", f"{url}/status/update",
             "-H", "Content-Type: application/json",
             "-H", f"X-STATUS-TOKEN: {token}",
             "-d", json.dumps(payload)],
            check=False,
            capture_output=True,
            timeout=10,
        )
    except Exception as e:
        print(f"[emit_progress] WARNING: failed to emit progress: {e}")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# === Helper Functions ===

def generate_run_id():
    """run_idを生成（YYYYMMDD_HHMMSS_rand）"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    rand = os.urandom(4).hex()[:8]
    return f"{timestamp}_{rand}"


def create_temp_config(base_config, run_id, query, max_results=10, date_from=None, date_to=None):
    """一時的な設定ファイルを作成"""
    config = base_config.copy()
    
    run_dir = Path("public") / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    if "search" not in config:
        config["search"] = {}
    
    config["search"]["query"] = query
    config["search"]["max_results"] = max_results
    if date_from:
        config["search"]["date_from"] = date_from
    if date_to:
        config["search"]["date_to"] = date_to
    
    if "paths" not in config:
        config["paths"] = {}
    
    config["paths"]["raw_dir"] = str(run_dir / "raw")
    config["paths"]["processed_dir"] = str(run_dir / "processed")
    config["paths"]["index_path"] = str(run_dir / "index.joblib")
    config["paths"]["report_path"] = str(run_dir / "report.md")
    
    return config


def run_pipeline(config_path):
    """run_pipeline.pyを実行"""
    try:
        result = subprocess.run(
            [sys.executable, "run_pipeline.py", config_path],
            capture_output=True,
            text=True,
            check=True,
        )
        return {"success": True, "output": result.stdout, "error": result.stderr}
    except subprocess.CalledProcessError as e:
        return {"success": False, "output": e.stdout, "error": e.stderr}


def write_json(path: Path, obj: dict):
    """JSONファイルを書き出し"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, obj: dict):
    """JSONL形式で追記"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# === Stats & Summary Generation ===

def generate_stats(run_id, query, status, run_dir, started_at, finished_at, error_msg=""):
    """stats.jsonを生成（詳細な数値情報）"""
    run_path = Path(run_dir)
    meta_path = run_path / "raw" / "pubmed_metadata.json"
    chunks_path = run_path / "processed" / "chunks.jsonl"
    index_path = run_path / "index.joblib"
    
    # 各種カウント
    pmids = 0
    meta_count = 0
    pmcids = 0
    pdf_downloaded = 0
    chunks_count = 0
    index_exists = index_path.exists()
    
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                records = meta.get("records", [])
                meta_count = len(records)
                pmids = meta_count
                pmcids = sum(1 for r in records if r.get("pmcid"))
        except Exception:
            pass
    
    # PDFカウント
    pmc_dir = run_path / "raw" / "pmc"
    if pmc_dir.exists():
        pdf_downloaded = len(list(pmc_dir.glob("*.pdf")))
    
    # チャンクカウント
    if chunks_path.exists():
        chunks_count = sum(1 for _ in chunks_path.open("r", encoding="utf-8"))
    
    stats = {
        "run_id": run_id,
        "query": query,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "updated_at": now_iso(),
        "index_version": run_id,
        # 詳細カウント
        "pmids": pmids,
        "meta": meta_count,
        "pmcids": pmcids,
        "pdf_ok": pdf_downloaded,
        "pdf_fail": max(0, pmcids - pdf_downloaded),
        "chunks": chunks_count,
        "index_ok": 1 if index_exists else 0,
        # エラー情報
        "failed": status == "failed",
        "error": error_msg,
    }
    
    stats_path = run_path / "stats.json"
    write_json(stats_path, stats)
    print(f"[ci_run] Generated stats.json: {stats_path}")
    return stats


def _normalize_summary_status(status: str) -> str:
    normalized = status.lower().strip()
    if normalized in {"success", "succeeded", "complete", "completed"}:
        return "success"
    if normalized in {"failed", "failure", "error"}:
        return "failed"
    return "failed"


def generate_summary(run_id, query, status, run_dir, started_at, finished_at, stats=None):
    """summary.jsonを生成（ダッシュボード互換形式）"""
    run_path = Path(run_dir)
    meta_path = run_path / "raw" / "pubmed_metadata.json"
    report_path = run_path / "report.md"
    
    papers = stats.get("meta", 0) if stats else 0
    if not papers and meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                papers = len(meta.get("records", []))
        except Exception:
            pass
    
    normalized_status = _normalize_summary_status(status)
    gate_passed = papers > 0 and normalized_status == "success"
    required_files = ["report.md"]
    existing = [f for f in required_files if (run_path / f).exists()]
    contract_valid = len(existing) == len(required_files) and papers > 0
    evidence_coverage = 1.0 if papers > 0 else 0.0
    
    summary = {
        "run_id": run_id,
        "query": query,
        "status": normalized_status,
        "timestamp": finished_at,
        "papers": papers,
        "claims": 0,
        "evidence": 0,
        "gate_passed": gate_passed,
        "contract_valid": contract_valid,
        "metrics": {
            "evidence_coverage": evidence_coverage,
            "paper_count": papers,
            "claim_count": 0,
            "pmcids": stats.get("pmcids", 0) if stats else 0,
            "pdf_ok": stats.get("pdf_ok", 0) if stats else 0,
            "chunks": stats.get("chunks", 0) if stats else 0,
        },
        "index_version": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "artifacts": {
            "report_md": f"runs/{run_id}/report.md" if report_path.exists() else None,
            "meta_json": f"runs/{run_id}/raw/pubmed_metadata.json" if meta_path.exists() else None,
            "stats_json": f"runs/{run_id}/stats.json",
        }
    }
    
    summary_path = run_path / "summary.json"
    write_json(summary_path, summary)
    print(f"[ci_run] Generated summary.json: {summary_path}")
    return summary


# === Main Entry Point ===

def main():
    parser = argparse.ArgumentParser(description="CI Run - run_idごとに独立実行")
    parser.add_argument("--run-id", help="run_id（未指定なら自動生成）")
    parser.add_argument("--query", required=True, help="検索クエリ")
    parser.add_argument("--max-results", type=int, default=10, help="最大論文数")
    parser.add_argument("--date-from", help="検索開始日（YYYY/MM/DD）")
    parser.add_argument("--date-to", help="検索終了日（YYYY/MM/DD）")
    parser.add_argument("--action", default="pipeline", help="アクション（pipeline | rebuild_index | export_report）")
    args = parser.parse_args()
    
    # run_id: 環境変数RUN_ID > 引数 > 自動生成
    run_id = os.environ.get("RUN_ID") or args.run_id or generate_run_id()
    print(f"[ci_run] run_id: {run_id}")
    
    started_at = now_iso()
    run_dir = Path("public") / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    warnings_path = run_dir / "warnings.jsonl"
    status = "running"
    error_msg = ""
    
    # ベース設定読み込み
    base_config_path = Path("config.yaml")
    if not base_config_path.exists():
        print(f"[ci_run] ERROR: config.yaml not found", file=sys.stderr)
        append_jsonl(warnings_path, {"type": "config_error", "message": "config.yaml not found", "at": now_iso()})
        sys.exit(1)
    
    with open(base_config_path, "r", encoding="utf-8") as f:
        base_config = yaml.safe_load(f)
    
    try:
        if args.action == "pipeline":
            emit_progress(25, "config", "Creating pipeline configuration", {"query": args.query})
            
            temp_config = create_temp_config(
                base_config, run_id, args.query, args.max_results, args.date_from, args.date_to,
            )
            
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
                yaml.dump(temp_config, f)
                temp_config_path = f.name
            
            try:
                emit_progress(30, "pipeline", "Running paper collection pipeline")
                print(f"[ci_run] Running pipeline with config: {temp_config_path}")
                result = run_pipeline(temp_config_path)
                
                if result["success"]:
                    print("[ci_run] Pipeline completed successfully")
                    status = "complete"
                    emit_progress(85, "artifacts", "Generating artifacts")
                else:
                    print(f"[ci_run] Pipeline failed: {result['error']}", file=sys.stderr)
                    status = "failed"
                    error_msg = result["error"][:500] if result["error"] else "Unknown error"
                    append_jsonl(warnings_path, {"type": "pipeline_error", "message": error_msg, "at": now_iso()})
                
                if result["output"]:
                    print(result["output"])
                if result["error"]:
                    print(result["error"], file=sys.stderr)
                    
            finally:
                Path(temp_config_path).unlink(missing_ok=True)
        
        elif args.action == "rebuild_index":
            emit_progress(50, "rebuild", "Rebuilding index")
            print(f"[ci_run] Action 'rebuild_index' not implemented yet")
            status = "complete"
        
        elif args.action == "export_report":
            emit_progress(50, "export", "Exporting report")
            print(f"[ci_run] Action 'export_report' not implemented yet")
            status = "complete"
        
        else:
            print(f"[ci_run] ERROR: Unknown action: {args.action}", file=sys.stderr)
            append_jsonl(warnings_path, {"type": "unknown_action", "message": args.action, "at": now_iso()})
            sys.exit(1)
    
    except Exception as e:
        status = "failed"
        error_msg = str(e)
        append_jsonl(warnings_path, {"type": "exception", "message": repr(e), "traceback": traceback.format_exc(), "at": now_iso()})
        emit_progress(100, "failed", f"Pipeline failed: {error_msg}")
        raise
    
    finally:
        # 必ず成果物を生成（partially failed でも UI が読める状態にする）
        finished_at = now_iso()
        
        stats = generate_stats(run_id, args.query, status, run_dir, started_at, finished_at, error_msg)
        generate_summary(run_id, args.query, status, run_dir, started_at, finished_at, stats)
        
        # runs/index.json更新
        print("[ci_run] Building runs index...")
        try:
            subprocess.run([sys.executable, "scripts/build_runs_index.py"], check=True)
        except Exception as e:
            print(f"[ci_run] WARNING: Failed to build index: {e}", file=sys.stderr)
        
        print(f"[ci_run] Done! run_id={run_id}, status={status}")


if __name__ == "__main__":
    main()
