"""Run Store - unified storage for run artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


class RunStore:
    """Manages all artifacts for a single run.

    Directory structure:
        logs/runs/{run_id}/
            ├── events.jsonl
            ├── run_config.json
            ├── result.json
            └── eval_summary.json
    """

    def __init__(self, run_id: str, base_dir: str = "logs/runs"):
        self.run_id = run_id
        self.base_dir = Path(base_dir)
        self.run_dir = self.base_dir / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

    @property
    def events_file(self) -> Path:
        return self.run_dir / "events.jsonl"

    @property
    def config_file(self) -> Path:
        return self.run_dir / "run_config.json"

    @property
    def result_file(self) -> Path:
        return self.run_dir / "result.json"

    @property
    def eval_file(self) -> Path:
        return self.run_dir / "eval_summary.json"

    def save_config(self, config: dict) -> None:
        """Save run configuration."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def save_result(self, result: dict) -> None:
        """Save run result."""
        with open(self.result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def save_eval(self, eval_summary: dict) -> None:
        """Save evaluation summary."""
        with open(self.eval_file, "w", encoding="utf-8") as f:
            json.dump(eval_summary, f, indent=2, ensure_ascii=False)

    def load_config(self) -> Optional[dict]:
        """Load run configuration."""
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def load_result(self) -> Optional[dict]:
        """Load run result."""
        if self.result_file.exists():
            with open(self.result_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def load_eval(self) -> Optional[dict]:
        """Load evaluation summary."""
        if self.eval_file.exists():
            with open(self.eval_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def get_summary(self) -> dict:
        """Get a summary of the run."""
        return {
            "run_id": self.run_id,
            "run_dir": str(self.run_dir),
            "has_events": self.events_file.exists(),
            "has_config": self.config_file.exists(),
            "has_result": self.result_file.exists(),
            "has_eval": self.eval_file.exists(),
        }

    @classmethod
    def list_runs(cls, base_dir: str = "logs/runs") -> list[str]:
        """List all run IDs."""
        base = Path(base_dir)
        if not base.exists():
            return []
        return [d.name for d in sorted(base.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)]

    @classmethod
    def get_latest(cls, base_dir: str = "logs/runs") -> Optional["RunStore"]:
        """Get the most recent run."""
        runs = cls.list_runs(base_dir)
        if runs:
            return cls(runs[0], base_dir)
        return None
