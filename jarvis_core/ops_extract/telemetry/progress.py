"""Progress emitter for ops_extract and related workflows."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .eta import ETAEstimator
from .models import ProgressPoint


STAGE_WEIGHT_MAP = {
    "preflight": 5.0,
    "ingest": 10.0,
    "ocr": 25.0,
    "extract": 25.0,
    "sync": 20.0,
    "retention_report": 15.0,
}

STAGE_CATEGORY_MAP = {
    "preflight": "preflight",
    "discover_inputs": "ingest",
    "extract_text_pdf": "extract",
    "needs_ocr_decision": "ocr",
    "rasterize_pdf": "ocr",
    "ocr_yomitoku": "ocr",
    "normalize_text": "extract",
    "extract_figures_tables": "extract",
    "compute_metrics_warnings": "extract",
    "write_contract_files": "extract",
    "enqueue_drive_sync": "sync",
    "retention_mark": "retention_report",
    "survey_discover": "ingest",
    "survey_download": "sync",
    "survey_parse": "extract",
    "survey_index": "extract",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProgressEmitter:
    """Append progress points to progress.jsonl with weighted overall progress."""

    def __init__(
        self,
        run_dir: Path,
        *,
        eta_estimator: ETAEstimator | None = None,
        filename: str = "progress.jsonl",
    ) -> None:
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / filename
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.eta = eta_estimator or ETAEstimator(
            self.run_dir.parent if self.run_dir.parent else None
        )
        self._run_started = time.perf_counter()
        self._stage_state: dict[str, dict[str, Any]] = {}
        self._category_progress = {key: 0.0 for key in STAGE_WEIGHT_MAP}

    def emit_stage_start(self, stage: str, items_total: int | None = None) -> None:
        total = int(items_total) if items_total is not None and int(items_total) > 0 else 0
        self._stage_state[stage] = {
            "items_done": 0,
            "items_total": total,
            "progress": 0.0,
        }
        self._emit(stage)

    def emit_stage_update(
        self, stage: str, items_done: int, items_total: int | None = None
    ) -> None:
        state = self._stage_state.setdefault(
            stage, {"items_done": 0, "items_total": 0, "progress": 0.0}
        )
        if items_total is not None and int(items_total) > 0:
            state["items_total"] = int(items_total)
        state["items_done"] = max(0, int(items_done))
        total = int(state.get("items_total", 0))
        if total > 0:
            stage_progress = min(100.0, max(0.0, (state["items_done"] / total) * 100.0))
        else:
            # Fallback when total is unknown: monotonic coarse progress.
            stage_progress = min(99.0, float(state.get("progress", 0.0)) + 5.0)
        state["progress"] = stage_progress
        self._emit(stage)

    def emit_stage_end(self, stage: str) -> None:
        state = self._stage_state.setdefault(
            stage, {"items_done": 0, "items_total": 0, "progress": 0.0}
        )
        total = int(state.get("items_total", 0))
        if total <= 0:
            total = max(1, int(state.get("items_done", 0)))
            state["items_total"] = total
        state["items_done"] = total
        state["progress"] = 100.0
        self._emit(stage)

    def _emit(self, stage: str) -> None:
        state = self._stage_state.get(stage, {"items_done": 0, "items_total": 0, "progress": 0.0})
        stage_progress = float(state.get("progress", 0.0))
        category = STAGE_CATEGORY_MAP.get(stage, "extract")
        self._category_progress[category] = max(
            self._category_progress.get(category, 0.0), stage_progress
        )
        overall = self._overall_progress()
        elapsed = max(0.0, time.perf_counter() - self._run_started)
        eta_seconds, eta_confidence = self.eta.estimate(
            elapsed_seconds=elapsed,
            overall_progress_percent=overall,
        )

        point = ProgressPoint(
            ts_iso=_now_iso(),
            stage=stage,
            stage_progress_percent=round(stage_progress, 4),
            overall_progress_percent=round(overall, 4),
            items_done=int(state.get("items_done", 0)),
            items_total=int(state.get("items_total", 0)),
            eta_seconds=(round(eta_seconds, 4) if eta_seconds is not None else None),
            eta_confidence_percent=round(eta_confidence, 2),
        )
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(point.__dict__, ensure_ascii=False) + "\n")

    def _overall_progress(self) -> float:
        total = 0.0
        for category, weight in STAGE_WEIGHT_MAP.items():
            progress = max(0.0, min(100.0, float(self._category_progress.get(category, 0.0))))
            total += weight * (progress / 100.0)
        return max(0.0, min(100.0, total))
