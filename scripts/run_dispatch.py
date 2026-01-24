# scripts/run_dispatch.py
from __future__ import annotations
import json, os, time
from pathlib import Path
from datetime import datetime, timezone

# 既存のjarvis_coreロジックをインポート
# プロジェクト構造に合わせて調整
try:
    from jarvis_core.app import run_task
except ImportError:
    # 開発環境やパス設定によっては必要
    import sys
    sys.path.append(os.path.abspath("."))
    from jarvis_core.app import run_task

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def main() -> int:
    run_id = os.environ.get("RUN_ID", "local-test")
    action = os.environ.get("ACTION", "report")
    query = os.environ.get("QUERY", "")
    max_papers = int(os.environ.get("MAX_PAPERS", "10"))

    # 出力先ベースディレクトリ (dashboard/ 配下に出して gh-pages にデプロイされる想定)
    base = Path("dashboard") / "runs" / run_id
    progress_path = base / "progress.json"
    summary_path = base / "summary.json"

    started = now_iso()
    
    # 初期進捗
    write_json(progress_path, {
        "schema_version": "runs.progress.v1",
        "run_id": run_id,
        "phase": "start",
        "percent": 0,
        "message": "starting",
        "updated_at": now_iso(),
    })

    try:
        # jarvis_core.app.run_task を呼び出す
        # action に応じてタスクを構築
        task_dict = {
            "goal": query or f"Perform {action}",
            "category": "generic",
            "action": action
        }
        
        config_dict = {
            "pipeline": "configs/pipelines/e2e_oa10.yml", # デフォルト
            "max_results": max_papers
        }
        
        print(f"Executing task: {query} (action={action})")
        
        # 中間進捗の更新（シミュレーションまたは実際のフェーズごと）
        write_json(progress_path, {
            "schema_version": "runs.progress.v1",
            "run_id": run_id,
            "phase": "executing",
            "percent": 50,
            "message": f"running action={action}",
            "updated_at": now_iso(),
        })

        # 実際のパイプライン実行
        result = run_task(task_dict, config_dict)
        
        # 成果物の保存
        artifacts = base / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)
        report = artifacts / "report.md"
        
        # 結果からレポート内容を取得（resultオブジェクトの仕様に合わせる）
        report_content = getattr(result, "answer", f"# RUN {run_id}\n\naction={action}\nquery={query}\n")
        report.write_text(report_content, encoding="utf-8")

        finished = now_iso()
        
        # 完了進捗
        write_json(progress_path, {
            "schema_version": "runs.progress.v1",
            "run_id": run_id,
            "phase": "done",
            "percent": 100,
            "message": "succeeded",
            "updated_at": finished,
        })
        
        # サマリー
        write_json(summary_path, {
            "schema_version": "runs.summary.v1",
            "run_id": run_id,
            "status": "succeeded",
            "started_at": started,
            "finished_at": finished,
            "action": action,
            "inputs": {"query": query, "max_papers": max_papers},
            "outputs": {"report_path": str(report.relative_to(Path("dashboard"))).replace("\\", "/")},
            "metrics": {
                "papers": len(getattr(result, "citations", [])),
                "chunks": 0,
                "elapsed_sec": 0
            },
            "errors": [],
        })
        return 0

    except Exception as e:
        finished = now_iso()
        print(f"Error during execution: {e}")
        
        write_json(progress_path, {
            "schema_version": "runs.progress.v1",
            "run_id": run_id,
            "phase": "failed",
            "percent": 100,
            "message": str(e),
            "updated_at": finished,
        })
        
        write_json(summary_path, {
            "schema_version": "runs.summary.v1",
            "run_id": run_id,
            "status": "failed",
            "started_at": started,
            "finished_at": finished,
            "action": action,
            "inputs": {"query": query, "max_papers": max_papers},
            "outputs": {},
            "metrics": {"papers": 0, "chunks": 0, "elapsed_sec": 0},
            "errors": [repr(e)],
        })
        raise

if __name__ == "__main__":
    import sys
    sys.exit(main())
