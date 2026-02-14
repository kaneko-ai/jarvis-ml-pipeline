"""ETA estimator for ops_extract progress telemetry."""

from __future__ import annotations

import json
import statistics
from pathlib import Path


class ETAEstimator:
    """Estimate remaining runtime and confidence using history + current pace."""

    def __init__(self, runs_base: Path | None = None) -> None:
        self.runs_base = Path(runs_base) if runs_base else None
        self._history_seconds = self._load_history_seconds(limit=400)

    def _load_history_seconds(self, *, limit: int) -> list[float]:
        if not self.runs_base or not self.runs_base.exists():
            return []
        durations: list[float] = []
        for metrics_path in sorted(self.runs_base.glob("*/metrics.json"), reverse=True):
            try:
                payload = json.loads(metrics_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            value = payload.get("run_duration_sec")
            try:
                dur = float(value)
            except Exception:
                continue
            if dur > 0:
                durations.append(dur)
            if len(durations) >= limit:
                break
        return durations

    def estimate(
        self,
        *,
        elapsed_seconds: float,
        overall_progress_percent: float,
    ) -> tuple[float | None, float]:
        progress = max(0.0, min(100.0, float(overall_progress_percent)))
        elapsed = max(0.0, float(elapsed_seconds))
        if progress <= 0.0:
            return None, self._confidence()

        pace_eta = elapsed * (100.0 - progress) / progress
        history = self._history_seconds
        if not history:
            return pace_eta, 45.0

        baseline_total = statistics.median(history)
        baseline_eta = baseline_total * (100.0 - progress) / 100.0
        eta_seconds = (pace_eta * 0.7) + (baseline_eta * 0.3)
        return max(0.0, eta_seconds), self._confidence()

    def _confidence(self) -> float:
        history = self._history_seconds
        n = len(history)
        if n == 0:
            return 35.0
        if n == 1:
            return 45.0
        mean = sum(history) / n
        if mean <= 0:
            return 40.0
        try:
            std = statistics.pstdev(history)
        except Exception:
            std = 0.0
        cv = std / mean if mean else 1.0
        sample_score = min(1.0, n / 20.0)
        variance_score = max(0.0, 1.0 - min(1.0, cv))
        confidence = (0.6 * sample_score + 0.4 * variance_score) * 100.0
        return round(max(20.0, min(95.0, confidence)), 2)
