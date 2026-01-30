"""
JARVIS API (Log Contract Only)

Step 81-90: API/UIはログ契約にぶら下げる
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RunAPI:
    """Run API（ログ契約のみ）.

    Step 81-82: APIはrun_idを返すだけ、result.jsonを返すだけ
    """

    def __init__(self, runs_dir: str = "logs/runs"):
        """初期化."""
        self.runs_dir = Path(runs_dir)

    def start_run(self, config: dict[str, Any]) -> dict[str, str]:
        """runを開始（Step 81: run_idを返すだけ）."""
        from jarvis_core.storage.run_store_v2 import RunStore

        store = RunStore(str(self.runs_dir))
        ctx = store.create_run()
        ctx.save_config(config)

        return {"run_id": ctx.run_id}

    def get_status(self, run_id: str) -> dict[str, Any] | None:
        """ステータスを取得（Step 82: result.jsonを返すだけ）."""
        result_path = self.runs_dir / run_id / "result.json"

        if not result_path.exists():
            return None

        with open(result_path, encoding="utf-8") as f:
            return json.load(f)

    def get_eval_summary(self, run_id: str) -> dict[str, Any] | None:
        """eval_summaryを取得（Step 86）."""
        eval_path = self.runs_dir / run_id / "eval_summary.json"

        if not eval_path.exists():
            return None

        with open(eval_path, encoding="utf-8") as f:
            return json.load(f)

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        """run一覧を取得."""
        runs = []

        for run_dir in sorted(self.runs_dir.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue

            run_info = {"run_id": run_dir.name}

            # result.jsonがあれば読む
            result_path = run_dir / "result.json"
            if result_path.exists():
                with open(result_path, encoding="utf-8") as f:
                    result = json.load(f)
                run_info["status"] = result.get("status", "unknown")
                run_info["timestamp"] = result.get("timestamp")

            runs.append(run_info)

            if len(runs) >= limit:
                break

        return runs


class UIDataProvider:
    """UIデータプロバイダー.

    Step 83-90: UIはlogs/runsを読むだけ（UIが判定しない）
    """

    def __init__(self, runs_dir: str = "logs/runs"):
        """初期化."""
        self.runs_dir = Path(runs_dir)

    def get_run_display(self, run_id: str) -> dict[str, Any]:
        """UI表示用データを取得."""
        run_dir = self.runs_dir / run_id

        if not run_dir.exists():
            return {"error": "Run not found"}

        display = {"run_id": run_id}

        # result.json
        result_path = run_dir / "result.json"
        if result_path.exists():
            with open(result_path, encoding="utf-8") as f:
                result = json.load(f)
            display["status"] = result.get("status")
            display["answer"] = result.get("answer", "")[:500]
            display["citations"] = result.get("citations", [])

        # eval_summary.json（Step 84, 86）
        eval_path = run_dir / "eval_summary.json"
        if eval_path.exists():
            with open(eval_path, encoding="utf-8") as f:
                eval_data = json.load(f)
            display["gate_passed"] = eval_data.get("gate_passed")
            display["fail_reasons"] = eval_data.get("fail_reasons", [])
            display["metrics"] = eval_data.get("metrics", {})

        # papers.jsonl（Step 85）
        papers_path = run_dir / "papers.jsonl"
        if papers_path.exists():
            papers = []
            with open(papers_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        papers.append(json.loads(line))
            display["papers"] = papers

        # warnings.jsonl
        warnings_path = run_dir / "warnings.jsonl"
        if warnings_path.exists():
            warnings = []
            with open(warnings_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        warnings.append(json.loads(line))
            display["warnings"] = warnings

        # Bundle完全性（Step 87-88）
        required_files = [
            "input.json",
            "run_config.json",
            "result.json",
            "eval_summary.json",
            "papers.jsonl",
            "claims.jsonl",
            "evidence.jsonl",
            "scores.json",
            "report.md",
            "warnings.jsonl",
        ]
        display["bundle_status"] = {f: (run_dir / f).exists() for f in required_files}
        display["bundle_complete"] = all(display["bundle_status"].values())

        return display
