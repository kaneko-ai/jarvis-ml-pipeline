"""Run Store - unified storage for run artifacts.

Per MASTER_SPEC v1.2 (DEC-006):
- 成果物契約: 10ファイル必須
- パス決定権はRunStoreのみが持つ
"""

from __future__ import annotations

import json
from pathlib import Path


class RunStore:
    """Manages all artifacts for a single run.

    Directory structure (per MASTER_SPEC v1.2):
        logs/runs/{run_id}/
            ├── input.json          # 実行条件
            ├── run_config.json     # 実行設定
            ├── papers.jsonl        # 論文メタ
            ├── claims.jsonl        # 主張
            ├── evidence.jsonl      # 根拠
            ├── scores.json         # スコア
            ├── result.json         # 実行結果
            ├── eval_summary.json   # 評価結果
            ├── warnings.jsonl      # 警告
            └── report.md           # 人間向けレポート
    """

    # 必須成果物（per MASTER_SPEC v1.2 / DEC-006）
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

    # 失敗時でも必須（最低限のファイル）
    FAILURE_REQUIRED = [
        "result.json",
        "eval_summary.json",
        "warnings.jsonl",
        "report.md",
    ]

    def __init__(self, run_id: str, base_dir: str = "logs/runs"):
        self.run_id = run_id
        self.base_dir = Path(base_dir)
        self.run_dir = self.base_dir / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

    # === File Properties ===
    @property
    def input_file(self) -> Path:
        return self.run_dir / "input.json"

    @property
    def config_file(self) -> Path:
        return self.run_dir / "run_config.json"

    @property
    def papers_file(self) -> Path:
        return self.run_dir / "papers.jsonl"

    @property
    def claims_file(self) -> Path:
        return self.run_dir / "claims.jsonl"

    @property
    def evidence_file(self) -> Path:
        return self.run_dir / "evidence.jsonl"

    @property
    def scores_file(self) -> Path:
        return self.run_dir / "scores.json"

    @property
    def result_file(self) -> Path:
        return self.run_dir / "result.json"

    @property
    def eval_file(self) -> Path:
        return self.run_dir / "eval_summary.json"

    @property
    def warnings_file(self) -> Path:
        return self.run_dir / "warnings.jsonl"

    @property
    def report_file(self) -> Path:
        return self.run_dir / "report.md"

    # Optional files (Phase 2+)
    @property
    def cost_report_file(self) -> Path:
        return self.run_dir / "cost_report.json"

    @property
    def features_file(self) -> Path:
        return self.run_dir / "features.jsonl"

    # Legacy alias for backward compatibility
    @property
    def events_file(self) -> Path:
        return self.run_dir / "events.jsonl"

    # === Save Methods ===
    def save_input(self, input_data: dict) -> None:
        """Save input specification."""
        with open(self.input_file, "w", encoding="utf-8") as f:
            json.dump(input_data, f, indent=2, ensure_ascii=False)

    def save_config(self, config: dict) -> None:
        """Save run configuration."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def save_papers(self, papers: list) -> None:
        """Save papers as JSONL."""
        with open(self.papers_file, "w", encoding="utf-8") as f:
            for paper in papers:
                f.write(json.dumps(paper, ensure_ascii=False) + "\n")

    def save_claims(self, claims: list) -> None:
        """Save claims as JSONL."""
        with open(self.claims_file, "w", encoding="utf-8") as f:
            for claim in claims:
                f.write(json.dumps(claim, ensure_ascii=False) + "\n")

    def save_evidence(self, evidence: list) -> None:
        """Save evidence as JSONL."""
        with open(self.evidence_file, "w", encoding="utf-8") as f:
            for ev in evidence:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    def save_scores(self, scores: dict) -> None:
        """Save scores."""
        with open(self.scores_file, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=2, ensure_ascii=False)

    def save_result(self, result: dict) -> None:
        """Save run result."""
        with open(self.result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def save_eval(self, eval_summary: dict) -> None:
        """Save evaluation summary."""
        with open(self.eval_file, "w", encoding="utf-8") as f:
            json.dump(eval_summary, f, indent=2, ensure_ascii=False)

    def save_warnings(self, warnings: list) -> None:
        """Save warnings as JSONL."""
        with open(self.warnings_file, "w", encoding="utf-8") as f:
            for warning in warnings:
                if isinstance(warning, str):
                    warning = {"code": "GENERAL", "message": warning, "severity": "warning"}
                f.write(json.dumps(warning, ensure_ascii=False) + "\n")

    def save_report(self, report: str) -> None:
        """Save markdown report."""
        with open(self.report_file, "w", encoding="utf-8") as f:
            f.write(report)

    def save_cost_report(self, cost_report: dict) -> None:
        """Save cost report (Phase 2 optional)."""
        with open(self.cost_report_file, "w", encoding="utf-8") as f:
            json.dump(cost_report, f, indent=2, ensure_ascii=False)

    def save_features(self, features: list) -> None:
        """Save rubric features as JSONL (Phase 2)."""
        with open(self.features_file, "w", encoding="utf-8") as f:
            for feature in features:
                f.write(json.dumps(feature, ensure_ascii=False) + "\n")

    # === Load Methods ===
    def load_config(self) -> dict | None:
        """Load run configuration."""
        if self.config_file.exists():
            with open(self.config_file, encoding="utf-8") as f:
                return json.load(f)
        return None

    def load_result(self) -> dict | None:
        """Load run result."""
        if self.result_file.exists():
            with open(self.result_file, encoding="utf-8") as f:
                return json.load(f)
        return None

    def load_eval(self) -> dict | None:
        """Load evaluation summary."""
        if self.eval_file.exists():
            with open(self.eval_file, encoding="utf-8") as f:
                return json.load(f)
        return None

    def load_papers(self) -> list:
        """Load papers."""
        if not self.papers_file.exists():
            return []
        with open(self.papers_file, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def load_claims(self) -> list:
        """Load claims."""
        if not self.claims_file.exists():
            return []
        with open(self.claims_file, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def load_evidence(self) -> list:
        """Load evidence."""
        if not self.evidence_file.exists():
            return []
        with open(self.evidence_file, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def load_warnings(self) -> list:
        """Load warnings."""
        if not self.warnings_file.exists():
            return []
        with open(self.warnings_file, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def load_cost_report(self) -> dict | None:
        """Load cost report (Phase 2 optional)."""
        if self.cost_report_file.exists():
            with open(self.cost_report_file, encoding="utf-8") as f:
                return json.load(f)
        return None

    def load_features(self) -> list:
        """Load rubric features (Phase 2)."""
        if not self.features_file.exists():
            return []
        with open(self.features_file, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    # === Validation ===
    def validate_contract(self, is_failure: bool = False) -> list[str]:
        """成果物契約の違反をチェック (per MASTER_SPEC v1.2).

        Args:
            is_failure: True if run failed (less strict requirements)

        Returns:
            欠損ファイル名のリスト。空なら契約遵守。
        """
        required = self.FAILURE_REQUIRED if is_failure else self.REQUIRED_ARTIFACTS
        missing = []
        for artifact in required:
            artifact_path = self.run_dir / artifact
            if not artifact_path.exists():
                missing.append(artifact)
        return missing

    def get_summary(self) -> dict:
        """Get a summary of the run."""
        result = self.load_result()
        is_failure = result is not None and result.get("status") != "success"
        missing = self.validate_contract(is_failure=is_failure)

        eval_data = self.load_eval()
        fail_reasons = []
        if eval_data:
            fail_reasons = eval_data.get("fail_reasons", [])

        return {
            "run_id": self.run_id,
            "run_dir": str(self.run_dir),
            "has_input": self.input_file.exists(),
            "has_config": self.config_file.exists(),
            "has_papers": self.papers_file.exists(),
            "has_claims": self.claims_file.exists(),
            "has_evidence": self.evidence_file.exists(),
            "has_scores": self.scores_file.exists(),
            "has_result": self.result_file.exists(),
            "has_eval": self.eval_file.exists(),
            "has_warnings": self.warnings_file.exists(),
            "has_report": self.report_file.exists(),
            "contract_valid": len(missing) == 0,
            "missing_artifacts": missing,
            "fail_reasons": fail_reasons,
        }

    @classmethod
    def list_runs(cls, base_dir: str = "logs/runs") -> list[str]:
        """List all run IDs."""
        base = Path(base_dir)
        if not base.exists():
            return []
        return [
            d.name for d in sorted(base.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        ]

    @classmethod
    def get_latest(cls, base_dir: str = "logs/runs") -> RunStore | None:
        """Get the most recent run."""
        runs = cls.list_runs(base_dir)
        if runs:
            return cls(runs[0], base_dir)
        return None
