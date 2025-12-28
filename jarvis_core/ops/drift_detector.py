"""ITER-10: 仕様凍結・劣化検知 (Spec Freeze & Drift Detection).

仕様の凍結と性能ドリフトの検知。
- スキーマ凍結
- 性能ベースライン
- ドリフトアラート
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SpecSnapshot:
    """仕様スナップショット."""
    spec_id: str
    version: str
    schema_hash: str
    created_at: str
    frozen: bool = False
    
    def to_dict(self) -> dict:
        return {
            "spec_id": self.spec_id,
            "version": self.version,
            "schema_hash": self.schema_hash,
            "created_at": self.created_at,
            "frozen": self.frozen,
        }


@dataclass
class DriftAlert:
    """ドリフトアラート."""
    metric_name: str
    baseline_value: float
    current_value: float
    drift_percent: float
    severity: str  # low, medium, high, critical
    timestamp: str
    
    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "drift_percent": self.drift_percent,
            "severity": self.severity,
            "timestamp": self.timestamp,
        }


class SpecFreezer:
    """仕様凍結器.
    
    仕様をスナップショットとして保存し、変更を検知。
    """
    
    def __init__(self, spec_dir: Optional[Path] = None):
        self.spec_dir = spec_dir or Path("specs")
        self._snapshots: Dict[str, SpecSnapshot] = {}
        self._load_snapshots()
    
    def _load_snapshots(self) -> None:
        """スナップショットを読み込み."""
        snapshot_file = self.spec_dir / "frozen_specs.json"
        if snapshot_file.exists():
            try:
                with open(snapshot_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for key, val in data.items():
                    self._snapshots[key] = SpecSnapshot(**val)
            except Exception:
                pass
    
    def _save_snapshots(self) -> None:
        """スナップショットを保存."""
        self.spec_dir.mkdir(parents=True, exist_ok=True)
        snapshot_file = self.spec_dir / "frozen_specs.json"
        
        data = {k: v.to_dict() for k, v in self._snapshots.items()}
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def freeze(
        self,
        spec_id: str,
        schema: Dict[str, Any],
        version: str = "1.0",
    ) -> SpecSnapshot:
        """仕様を凍結."""
        schema_json = json.dumps(schema, sort_keys=True)
        schema_hash = hashlib.sha256(schema_json.encode()).hexdigest()[:16]
        
        snapshot = SpecSnapshot(
            spec_id=spec_id,
            version=version,
            schema_hash=schema_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
            frozen=True,
        )
        
        self._snapshots[spec_id] = snapshot
        self._save_snapshots()
        
        return snapshot
    
    def check(
        self,
        spec_id: str,
        schema: Dict[str, Any],
    ) -> bool:
        """凍結された仕様と一致するか確認."""
        if spec_id not in self._snapshots:
            return True  # 凍結されていない
        
        snapshot = self._snapshots[spec_id]
        if not snapshot.frozen:
            return True
        
        schema_json = json.dumps(schema, sort_keys=True)
        current_hash = hashlib.sha256(schema_json.encode()).hexdigest()[:16]
        
        return current_hash == snapshot.schema_hash
    
    def list_frozen(self) -> List[SpecSnapshot]:
        """凍結された仕様一覧."""
        return [s for s in self._snapshots.values() if s.frozen]


class DriftDetector:
    """ドリフト検知器.
    
    性能メトリクスのドリフトを検知。
    """
    
    DRIFT_THRESHOLDS = {
        "low": 0.05,      # 5%
        "medium": 0.10,   # 10%
        "high": 0.20,     # 20%
        "critical": 0.30, # 30%
    }
    
    def __init__(self, baseline_path: Optional[Path] = None):
        self.baseline_path = baseline_path or Path("evals/performance_baseline.json")
        self._baselines: Dict[str, float] = {}
        self._alerts: List[DriftAlert] = []
        self._load_baselines()
    
    def _load_baselines(self) -> None:
        """ベースラインを読み込み."""
        if self.baseline_path.exists():
            try:
                with open(self.baseline_path, "r", encoding="utf-8") as f:
                    self._baselines = json.load(f)
            except Exception:
                pass
    
    def _save_baselines(self) -> None:
        """ベースラインを保存."""
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_path, "w", encoding="utf-8") as f:
            json.dump(self._baselines, f, indent=2)
    
    def set_baseline(self, metric_name: str, value: float) -> None:
        """ベースラインを設定."""
        self._baselines[metric_name] = value
        self._save_baselines()
    
    def detect(
        self,
        metrics: Dict[str, float],
    ) -> List[DriftAlert]:
        """ドリフトを検知."""
        alerts = []
        
        for metric_name, current_value in metrics.items():
            if metric_name not in self._baselines:
                continue
            
            baseline = self._baselines[metric_name]
            if baseline == 0:
                continue
            
            drift = abs(current_value - baseline) / baseline
            
            # 深刻度判定
            severity = "low"
            for level, threshold in sorted(
                self.DRIFT_THRESHOLDS.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                if drift >= threshold:
                    severity = level
                    break
            
            # 閾値以上のみアラート
            if drift >= self.DRIFT_THRESHOLDS["low"]:
                alert = DriftAlert(
                    metric_name=metric_name,
                    baseline_value=baseline,
                    current_value=current_value,
                    drift_percent=drift * 100,
                    severity=severity,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                alerts.append(alert)
                self._alerts.append(alert)
        
        return alerts
    
    def get_all_alerts(self) -> List[DriftAlert]:
        """全アラートを取得."""
        return self._alerts


def freeze_spec(
    spec_id: str,
    schema: Dict[str, Any],
    version: str = "1.0",
) -> SpecSnapshot:
    """便利関数: 仕様を凍結."""
    freezer = SpecFreezer()
    return freezer.freeze(spec_id, schema, version)


def detect_drift(metrics: Dict[str, float]) -> List[DriftAlert]:
    """便利関数: ドリフトを検知."""
    detector = DriftDetector()
    return detector.detect(metrics)
