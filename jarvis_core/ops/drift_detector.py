"""
JARVIS Model Drift Detection

M6: 長期信頼性のためのモデル劣化検知
- Goldenテスト回帰
- 品質スコアトレンド
- アラート生成
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class GoldenTestCase:
    """Goldenテストケース."""
    test_id: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    tolerance: float = 0.05
    critical: bool = False
    description: str = ""


@dataclass
class GoldenTestResult:
    """Goldenテスト結果."""
    test_id: str
    passed: bool
    similarity_score: float
    expected_keys: List[str]
    actual_keys: List[str]
    differences: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class DriftAlert:
    """劣化アラート."""
    alert_id: str
    severity: str  # low, medium, high, critical
    metric_name: str
    current_value: float
    baseline_value: float
    threshold: float
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class GoldenTestRunner:
    """Goldenテストランナー."""
    
    def __init__(self, golden_dir: str = "tests/golden"):
        """
        初期化.
        
        Args:
            golden_dir: Goldenテストデータディレクトリ
        """
        self.golden_dir = Path(golden_dir)
        self.golden_dir.mkdir(parents=True, exist_ok=True)
    
    def load_test_cases(self) -> List[GoldenTestCase]:
        """テストケースを読み込み."""
        cases = []
        golden_file = self.golden_dir / "golden_cases.json"
        
        if not golden_file.exists():
            return cases
        
        with open(golden_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data.get("cases", []):
            cases.append(GoldenTestCase(
                test_id=item["test_id"],
                input_data=item["input_data"],
                expected_output=item["expected_output"],
                tolerance=item.get("tolerance", 0.05),
                critical=item.get("critical", False),
                description=item.get("description", "")
            ))
        
        return cases
    
    def save_test_cases(self, cases: List[GoldenTestCase]):
        """テストケースを保存."""
        golden_file = self.golden_dir / "golden_cases.json"
        
        with open(golden_file, 'w', encoding='utf-8') as f:
            json.dump({
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "cases": [asdict(c) for c in cases]
            }, f, ensure_ascii=False, indent=2)
    
    def compare_outputs(
        self, 
        expected: Dict[str, Any], 
        actual: Dict[str, Any],
        tolerance: float = 0.05
    ) -> Tuple[float, List[str]]:
        """
        出力を比較.
        
        Args:
            expected: 期待出力
            actual: 実際の出力
            tolerance: 許容誤差
        
        Returns:
            (類似度スコア, 差異リスト)
        """
        differences = []
        matches = 0
        total = 0
        
        # キーの比較
        expected_keys = set(expected.keys())
        actual_keys = set(actual.keys())
        
        missing_keys = expected_keys - actual_keys
        extra_keys = actual_keys - expected_keys
        
        if missing_keys:
            differences.append(f"Missing keys: {missing_keys}")
        if extra_keys:
            differences.append(f"Extra keys: {extra_keys}")
        
        # 値の比較
        for key in expected_keys & actual_keys:
            total += 1
            expected_val = expected[key]
            actual_val = actual.get(key)
            
            if isinstance(expected_val, (int, float)) and isinstance(actual_val, (int, float)):
                if abs(expected_val - actual_val) <= abs(expected_val * tolerance):
                    matches += 1
                else:
                    differences.append(f"{key}: expected {expected_val}, got {actual_val}")
            elif expected_val == actual_val:
                matches += 1
            else:
                differences.append(f"{key}: values differ")
        
        similarity = matches / total if total > 0 else 0.0
        return similarity, differences
    
    def run_test(
        self, 
        test_case: GoldenTestCase, 
        actual_output: Dict[str, Any]
    ) -> GoldenTestResult:
        """
        テストを実行.
        
        Args:
            test_case: テストケース
            actual_output: 実際の出力
        
        Returns:
            テスト結果
        """
        try:
            similarity, differences = self.compare_outputs(
                test_case.expected_output,
                actual_output,
                test_case.tolerance
            )
            
            passed = similarity >= (1.0 - test_case.tolerance)
            
            return GoldenTestResult(
                test_id=test_case.test_id,
                passed=passed,
                similarity_score=similarity,
                expected_keys=list(test_case.expected_output.keys()),
                actual_keys=list(actual_output.keys()),
                differences=differences
            )
        except Exception as e:
            return GoldenTestResult(
                test_id=test_case.test_id,
                passed=False,
                similarity_score=0.0,
                expected_keys=[],
                actual_keys=[],
                error=str(e)
            )


class DriftDetector:
    """劣化検知器."""
    
    def __init__(self, metrics_path: str = "artifacts/metrics_aggregate.jsonl"):
        """
        初期化.
        
        Args:
            metrics_path: メトリクス集約ファイルパス
        """
        self.metrics_path = Path(metrics_path)
        self.alerts: List[DriftAlert] = []
        self._alert_counter = 0
    
    def load_recent_metrics(self, window_size: int = 10) -> List[Dict[str, Any]]:
        """最近のメトリクスを読み込み."""
        if not self.metrics_path.exists():
            return []
        
        metrics = []
        with open(self.metrics_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    metrics.append(json.loads(line))
        
        return metrics[-window_size:]
    
    def calculate_baseline(self, metrics: List[Dict[str, Any]], metric_name: str) -> Optional[float]:
        """ベースライン値を計算."""
        values = []
        for m in metrics:
            if metric_name in m:
                values.append(m[metric_name])
            elif "quality" in m and metric_name in m.get("quality", {}):
                values.append(m["quality"][metric_name])
        
        if not values:
            return None
        
        return sum(values) / len(values)
    
    def check_drift(
        self,
        metric_name: str,
        current_value: float,
        baseline: float,
        threshold: float = 0.1
    ) -> Optional[DriftAlert]:
        """
        劣化をチェック.
        
        Args:
            metric_name: メトリクス名
            current_value: 現在の値
            baseline: ベースライン値
            threshold: 劣化閾値（相対）
        
        Returns:
            アラート（劣化検知時）
        """
        if baseline == 0:
            return None
        
        drift_ratio = (baseline - current_value) / baseline
        
        if drift_ratio > threshold:
            self._alert_counter += 1
            
            if drift_ratio > 0.3:
                severity = "critical"
            elif drift_ratio > 0.2:
                severity = "high"
            elif drift_ratio > 0.15:
                severity = "medium"
            else:
                severity = "low"
            
            alert = DriftAlert(
                alert_id=f"DRIFT-{self._alert_counter:04d}",
                severity=severity,
                metric_name=metric_name,
                current_value=current_value,
                baseline_value=baseline,
                threshold=threshold,
                message=f"{metric_name} degraded by {drift_ratio:.1%} from baseline"
            )
            
            self.alerts.append(alert)
            return alert
        
        return None
    
    def run_drift_check(self, current_metrics: Dict[str, float]) -> List[DriftAlert]:
        """
        全メトリクスの劣化チェックを実行.
        
        Args:
            current_metrics: 現在のメトリクス
        
        Returns:
            アラートリスト
        """
        recent = self.load_recent_metrics()
        alerts = []
        
        thresholds = {
            "provenance_rate": 0.05,
            "pico_consistency_rate": 0.10,
            "extraction_completeness": 0.10
        }
        
        for metric_name, current_value in current_metrics.items():
            baseline = self.calculate_baseline(recent, metric_name)
            if baseline is None:
                continue
            
            threshold = thresholds.get(metric_name, 0.10)
            alert = self.check_drift(metric_name, current_value, baseline, threshold)
            if alert:
                alerts.append(alert)
        
        return alerts
    
    def get_alerts(self) -> List[DriftAlert]:
        """アラートを取得."""
        return self.alerts
    
    def clear_alerts(self):
        """アラートをクリア."""
        self.alerts = []


# グローバルインスタンス
_drift_detector: Optional[DriftDetector] = None


def get_drift_detector() -> DriftDetector:
    """劣化検知器を取得."""
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = DriftDetector()
    return _drift_detector
