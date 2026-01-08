"""
JARVIS Run Store

Step 14-17: run_id生成、logs/runs管理、成果物契約
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# 必須ファイル（Bundle Contract）
REQUIRED_FILES = [
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


def generate_run_id() -> str:
    """run_id生成（規約固定）.
    
    Format: YYYYMMDD_HHMMSS_<uuid4[:8]>
    """
    now = datetime.now()
    date_part = now.strftime("%Y%m%d_%H%M%S")
    uuid_part = uuid.uuid4().hex[:8]
    return f"{date_part}_{uuid_part}"


class RunStore:
    """Run成果物ストア.
    
    logs/runs/{run_id}/ の唯一の管理者。
    成果物契約（Bundle Contract）を強制。
    """

    def __init__(self, base_dir: str = "logs/runs"):
        """初期化."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_run(self, run_id: str | None = None) -> RunContext:
        """新規runを作成."""
        if run_id is None:
            run_id = generate_run_id()

        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created run: {run_id}")
        return RunContext(run_id, run_dir)

    def get_run(self, run_id: str) -> RunContext | None:
        """既存runを取得."""
        run_dir = self.base_dir / run_id
        if run_dir.exists():
            return RunContext(run_id, run_dir)
        return None

    def list_runs(self, limit: int = 20) -> list[str]:
        """run一覧を取得."""
        runs = []
        for d in sorted(self.base_dir.iterdir(), reverse=True):
            if d.is_dir():
                runs.append(d.name)
                if len(runs) >= limit:
                    break
        return runs

    def validate_bundle(self, run_id: str) -> dict[str, bool]:
        """Bundle契約を検証."""
        run_dir = self.base_dir / run_id
        result = {}
        for f in REQUIRED_FILES:
            result[f] = (run_dir / f).exists()
        return result


class RunContext:
    """Run実行コンテキスト.
    
    成果物の読み書きを統一管理。
    """

    def __init__(self, run_id: str, run_dir: Path):
        """初期化."""
        self.run_id = run_id
        self.run_dir = run_dir

    def save_input(self, data: dict[str, Any]) -> None:
        """input.jsonを保存."""
        self._save_json("input.json", data)

    def save_config(self, data: dict[str, Any]) -> None:
        """run_config.jsonを保存."""
        data["run_id"] = self.run_id
        data["timestamp"] = datetime.now().isoformat()
        self._save_json("run_config.json", data)

    def save_result(self, data: dict[str, Any]) -> None:
        """result.jsonを保存（成功/失敗問わず必須）."""
        data["run_id"] = self.run_id
        data["timestamp"] = datetime.now().isoformat()
        self._save_json("result.json", data)

    def save_eval_summary(self, data: dict[str, Any]) -> None:
        """eval_summary.jsonを保存（成功/失敗問わず必須）."""
        data["run_id"] = self.run_id
        data["timestamp"] = datetime.now().isoformat()
        self._save_json("eval_summary.json", data)

    def save_papers(self, papers: list[dict[str, Any]]) -> None:
        """papers.jsonlを保存."""
        self._save_jsonl("papers.jsonl", papers)

    def save_claims(self, claims: list[dict[str, Any]]) -> None:
        """claims.jsonlを保存."""
        self._save_jsonl("claims.jsonl", claims)

    def save_evidence(self, evidence: list[dict[str, Any]]) -> None:
        """evidence.jsonlを保存."""
        self._save_jsonl("evidence.jsonl", evidence)

    def save_scores(self, data: dict[str, Any]) -> None:
        """scores.jsonを保存."""
        self._save_json("scores.json", data)

    def save_report(self, content: str) -> None:
        """report.mdを保存."""
        (self.run_dir / "report.md").write_text(content, encoding="utf-8")

    def save_warnings(self, warnings: list[dict[str, Any]]) -> None:
        """warnings.jsonlを保存."""
        self._save_jsonl("warnings.jsonl", warnings)

    def load_result(self) -> dict[str, Any] | None:
        """result.jsonを読み込み."""
        return self._load_json("result.json")

    def load_eval_summary(self) -> dict[str, Any] | None:
        """eval_summary.jsonを読み込み."""
        return self._load_json("eval_summary.json")

    def get_bundle_status(self) -> dict[str, bool]:
        """Bundle状態を取得."""
        return {f: (self.run_dir / f).exists() for f in REQUIRED_FILES}

    def is_complete(self) -> bool:
        """Bundle完全性チェック."""
        return all(self.get_bundle_status().values())

    def _save_json(self, filename: str, data: dict[str, Any]) -> None:
        """JSON保存."""
        path = self.run_dir / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_jsonl(self, filename: str, items: list[dict[str, Any]]) -> None:
        """JSONL保存."""
        path = self.run_dir / filename
        with open(path, 'w', encoding='utf-8') as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

    def _load_json(self, filename: str) -> dict[str, Any] | None:
        """JSON読み込み."""
        path = self.run_dir / filename
        if path.exists():
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        return None
