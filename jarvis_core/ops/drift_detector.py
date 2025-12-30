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
    message: str = ""
    
    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "drift_percent": self.drift_percent,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "message": self.message,
        }


@dataclass
class GoldenTestCase:
    """Goldenテストケース."""
    test_id: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    tolerance: float = 0.05


@dataclass
class GoldenTestResult:
    """Goldenテスト結果."""
    test_id: str
    passed: bool
    similarity: float
    differences: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())



class GoldenTestRunner:
    """Goldenテストランナー.
    
    期待される出力と実際の出力を比較し、回帰テストを実施。
    """
    
    def __init__(self, golden_dir: Optional[Path] = None):
        self.golden_dir = golden_dir or Path("evals/golden")
        self.golden_dir = Path(self.golden_dir)
        self._test_cases: Dict[str, GoldenTestCase] = {}
    
    def compare_outputs(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
        tolerance: float = 0.05,
    ) -> tuple[float, List[str]]:
        """出力を比較."""
        differences = []
        total_keys = set(expected.keys()) | set(actual.keys())
        
        if not total_keys:
            return 1.0, []
        
        matching_keys = 0
        
        for key in total_keys:
            if key not in expected:
                differences.append(f"Key '{key}' missing in expected")
                continue
            if key not in actual:
                differences.append(f"Key '{key}' missing in actual")
                continue
            
            exp_val = expected[key]
            act_val = actual[key]
            
            # 数値の比較（許容誤差あり）
            if isinstance(exp_val, (int, float)) and isinstance(act_val, (int, float)):
                if exp_val == 0:
                    if act_val == 0:
                        matching_keys += 1
                    else:
                        differences.append(f"Key '{key}': expected {exp_val}, got {act_val}")
                else:
                    rel_diff = abs(act_val - exp_val) / abs(exp_val)
                    if rel_diff <= tolerance:
                        matching_keys += 1
                    else:
                        differences.append(f"Key '{key}': expected {exp_val}, got {act_val} (diff: {rel_diff*100:.1f}%)")
            # その他の値の比較
            elif exp_val == act_val:
                matching_keys += 1
            else:
                differences.append(f"Key '{key}': expected {exp_val}, got {act_val}")
        
        similarity = matching_keys / len(total_keys) if total_keys else 1.0
        
        return similarity, differences
    
    def run_test(
        self,
        test_case: GoldenTestCase,
        actual_output: Dict[str, Any],
    ) -> GoldenTestResult:
        """テストを実行."""
        similarity, differences = self.compare_outputs(
            test_case.expected_output,
            actual_output,
            tolerance=test_case.tolerance,
        )
        
        passed = similarity >= 0.95  # 95%以上一致で合格
        
        return GoldenTestResult(
            test_id=test_case.test_id,
            passed=passed,
            similarity=similarity,
            differences=differences,
        )
    
    def save_golden(self, test_id: str, output: Dict[str, Any]) -> None:
        """Golden出力を保存."""
        self.golden_dir.mkdir(parents=True, exist_ok=True)
        golden_file = self.golden_dir / f"{test_id}.json"
        
        with open(golden_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    
    def load_golden(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Golden出力を読み込み."""
        golden_file = self.golden_dir / f"{test_id}.json"
        
        if not golden_file.exists():
            return None
        
        with open(golden_file, "r", encoding="utf-8") as f:
            return json.load(f)


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
    
    def __init__(self, baseline_path: Optional[Path] = None, metrics_path: Optional[Path] = None):
        # metrics_path は baseline_path のエイリアス（後方互換性）
        # 文字列の場合はPathに変換
        path = baseline_path or metrics_path
        if isinstance(path, str):
            path = Path(path)
        self.baseline_path = path or Path("evals/performance_baseline.json")
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
    
    def check_drift(
        self,
        metric_name: str,
        current_value: float,
        baseline: Optional[float] = None,
        threshold: float = 0.1,
    ) -> Optional[DriftAlert]:
        """ドリフトをチェック（単一メトリクス向け）."""
        # ベースラインが指定されていない場合は保存されているものを使用
        if baseline is None:
            if metric_name not in self._baselines:
                return None
            baseline = self._baselines[metric_name]
        
        if baseline == 0:
            return None
        
        drift = abs(current_value - baseline) / baseline
        
        # 閾値を超えていない場合はNone
        if drift < threshold:
            return None
        
        # 深刻度判定
        severity = "low"
        for level, thresh in sorted(
            self.DRIFT_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            if drift >= thresh:
                severity = level
                break
        
        alert = DriftAlert(
            metric_name=metric_name,
            baseline_value=baseline,
            current_value=current_value,
            drift_percent=drift * 100,
            severity=severity,
            timestamp=datetime.now(timezone.utc).isoformat(),
            message=f"{metric_name} drifted by {drift*100:.1f}% from baseline {baseline:.3f} to {current_value:.3f}",
        )
        self._alerts.append(alert)
        
        return alert


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
