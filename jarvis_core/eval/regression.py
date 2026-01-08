"""Prompt Regression (Q-03).

プロンプト変更による性能劣化を検出。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class BaselineScore:
    """ベースラインスコア."""
    prompt_id: str
    version: str
    prompt_hash: str
    metrics: dict[str, float]
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "hash": self.prompt_hash,
            "metrics": self.metrics,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> BaselineScore:
        return cls(
            prompt_id=d.get("prompt_id", ""),
            version=d.get("version", ""),
            prompt_hash=d.get("hash", ""),
            metrics=d.get("metrics", {}),
            created_at=d.get("created_at", ""),
        )


@dataclass
class RegressionResult:
    """リグレッション検出結果."""
    prompt_id: str
    passed: bool = True
    degraded_metrics: list[dict[str, Any]] = field(default_factory=list)
    improved_metrics: list[dict[str, Any]] = field(default_factory=list)
    baseline: BaselineScore | None = None
    current: dict[str, float] | None = None

    def to_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "passed": self.passed,
            "degraded_metrics": self.degraded_metrics,
            "improved_metrics": self.improved_metrics,
            "baseline": self.baseline.to_dict() if self.baseline else None,
            "current": self.current,
        }


class PromptRegressionChecker:
    """プロンプトリグレッション検出器.
    
    ベースラインスコアと比較して劣化を検出。
    """

    DEFAULT_THRESHOLDS = {
        "evidence_coverage": 0.95,  # 95%以上維持
        "locator_rate": 0.95,
        "citation_precision": 0.90,
        "provenance_rate": 0.95,
    }

    def __init__(
        self,
        baseline_path: Path | None = None,
        thresholds: dict[str, float] | None = None,
        tolerance: float = 0.05,  # 5%の劣化まで許容
    ):
        self.baseline_path = baseline_path or Path("evals/baseline_scores.json")
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
        self.tolerance = tolerance
        self._baselines: dict[str, BaselineScore] = {}
        self._load_baselines()

    def _load_baselines(self) -> None:
        """ベースラインを読み込み."""
        if not self.baseline_path.exists():
            return

        try:
            with open(self.baseline_path, encoding="utf-8") as f:
                data = json.load(f)

            for key, entry in data.items():
                self._baselines[key] = BaselineScore.from_dict(entry)
        except Exception:
            pass

    def _save_baselines(self) -> None:
        """ベースラインを保存."""
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            key: baseline.to_dict()
            for key, baseline in self._baselines.items()
        }

        with open(self.baseline_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def set_baseline(
        self,
        prompt_id: str,
        version: str,
        prompt_hash: str,
        metrics: dict[str, float],
    ) -> BaselineScore:
        """ベースラインを設定."""
        baseline = BaselineScore(
            prompt_id=prompt_id,
            version=version,
            prompt_hash=prompt_hash,
            metrics=metrics,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        key = f"{prompt_id}:{version}"
        self._baselines[key] = baseline
        self._save_baselines()

        return baseline

    def check(
        self,
        prompt_id: str,
        version: str,
        current_metrics: dict[str, float],
    ) -> RegressionResult:
        """リグレッションをチェック.
        
        Args:
            prompt_id: プロンプトID
            version: バージョン
            current_metrics: 現在のメトリクス
            
        Returns:
            RegressionResult
        """
        result = RegressionResult(
            prompt_id=prompt_id,
            current=current_metrics,
        )

        key = f"{prompt_id}:{version}"
        baseline = self._baselines.get(key)

        if not baseline:
            # ベースラインなし → PASS（初回）
            result.passed = True
            return result

        result.baseline = baseline

        # 各メトリクスを比較
        for metric_name, baseline_value in baseline.metrics.items():
            if metric_name not in current_metrics:
                continue

            current_value = current_metrics[metric_name]
            threshold_ratio = self.thresholds.get(metric_name, 0.95)

            # 許容される最低値
            min_allowed = baseline_value * threshold_ratio * (1 - self.tolerance)

            if current_value < min_allowed:
                # 劣化検出
                result.passed = False
                result.degraded_metrics.append({
                    "metric": metric_name,
                    "baseline": baseline_value,
                    "current": current_value,
                    "threshold": min_allowed,
                    "degradation_pct": ((baseline_value - current_value) / baseline_value) * 100,
                })
            elif current_value > baseline_value * 1.05:
                # 5%以上の改善
                result.improved_metrics.append({
                    "metric": metric_name,
                    "baseline": baseline_value,
                    "current": current_value,
                    "improvement_pct": ((current_value - baseline_value) / baseline_value) * 100,
                })

        return result

    def check_all(
        self,
        metrics_by_prompt: dict[str, dict[str, float]],
    ) -> list[RegressionResult]:
        """全プロンプトをチェック.
        
        Args:
            metrics_by_prompt: {prompt_id:version: metrics}
            
        Returns:
            結果リスト
        """
        results = []

        for key, current_metrics in metrics_by_prompt.items():
            parts = key.split(":")
            prompt_id = parts[0]
            version = parts[1] if len(parts) > 1 else "1.0"

            result = self.check(prompt_id, version, current_metrics)
            results.append(result)

        return results


def create_baseline_scores(
    output_path: Path = Path("evals/baseline_scores.json"),
) -> None:
    """初期ベースラインスコアを作成."""
    baseline_data = {
        "paper_survey_retrieve:1.0": {
            "prompt_id": "paper_survey_retrieve",
            "version": "1.0",
            "hash": "initial",
            "metrics": {
                "evidence_coverage": 0.95,
                "locator_rate": 0.98,
                "citation_precision": 0.90,
                "provenance_rate": 0.95,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "claim_extractor:1.0": {
            "prompt_id": "claim_extractor",
            "version": "1.0",
            "hash": "initial",
            "metrics": {
                "extraction_accuracy": 0.85,
                "type_accuracy": 0.80,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "evidence_extractor:1.0": {
            "prompt_id": "evidence_extractor",
            "version": "1.0",
            "hash": "initial",
            "metrics": {
                "evidence_coverage": 0.90,
                "locator_rate": 0.95,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(baseline_data, f, indent=2, ensure_ascii=False)


def check_regression(
    prompt_id: str,
    version: str,
    current_metrics: dict[str, float],
) -> RegressionResult:
    """便利関数: リグレッションをチェック."""
    checker = PromptRegressionChecker()
    return checker.check(prompt_id, version, current_metrics)
