from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from jarvis_core.runs.schema import RunProgress, RunSummary, RunStatus
from jarvis_core.runs.writer import RunWriter

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
    run_id = os.environ.get("RUN_ID", f"local-{int(datetime.now().timestamp())}")
    action = os.environ.get("ACTION", "report")
    query = os.environ.get("QUERY", "")
    max_papers = int(os.environ.get("MAX_PAPERS", "10"))

    # 出力先ベースディレクトリ
    base_dir = Path("dashboard") / "runs"
    writer = RunWriter(base_dir)
    run_dir = base_dir / run_id

    started_at = datetime.now(timezone.utc)

    # Initial Progress
    writer.write_progress(
        RunProgress(run_id=run_id, phase="start", percent=0.0, message="Initializing pipeline")
    )

    try:
        task_dict = {"goal": query or f"Perform {action}", "category": "generic", "action": action}
        config_dict = {
            "pipeline": "configs/pipelines/e2e_oa10.yml",
            "max_results": max_papers,
        }

        print(f"Executing run {run_id}: {query} (action={action})")

        writer.write_progress(
            RunProgress(
                run_id=run_id,
                phase="executing",
                percent=50.0,
                message=f"Executing action: {action}",
            )
        )

        # 実際のパイプライン実行
        result = run_task(task_dict, config_dict)

        # 成果物の保存
        artifacts_dir = run_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        report_path = artifacts_dir / "report.md"

        report_content = getattr(
            result, "answer", f"# RUN {run_id}\n\naction={action}\nquery={query}\n"
        )
        report_path.write_text(report_content, encoding="utf-8")

        finished_at = datetime.now(timezone.utc)

        # Success Progress
        writer.write_progress(
            RunProgress(
                run_id=run_id,
                phase="done",
                percent=100.0,
                message="Completed successfully",
                updated_at=finished_at,
            )
        )

        # Success Summary
        writer.write_summary(
            RunSummary(
                run_id=run_id,
                status=RunStatus.SUCCESS,
                started_at=started_at,
                finished_at=finished_at,
                metrics={
                    "papers": len(getattr(result, "citations", [])),
                    "chunks": 0,
                    "elapsed_sec": (finished_at - started_at).total_seconds(),
                },
                artifacts=[
                    {
                        "kind": "report",
                        "path": str(report_path.relative_to(Path("dashboard"))).replace("\\", "/"),
                    }
                ],
            )
        )
        return 0

    except Exception as e:
        finished_at = datetime.now(timezone.utc)
        print(f"Error during execution: {e}")

        writer.write_progress(
            RunProgress(
                run_id=run_id, phase="failed", percent=100.0, message=str(e), updated_at=finished_at
            )
        )

        writer.write_summary(
            RunSummary(
                run_id=run_id,
                status=RunStatus.FAILED,
                started_at=started_at,
                finished_at=finished_at,
                error=str(e),
                metrics={
                    "papers": 0,
                    "chunks": 0,
                    "elapsed_sec": (finished_at - started_at).total_seconds(),
                },
            )
        )
        raise


if __name__ == "__main__":
    import sys

    sys.exit(main())
