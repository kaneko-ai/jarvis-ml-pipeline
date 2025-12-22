"""Automated Eval Pipeline.

Per RP-370, implements automated evaluation pipeline.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path


@dataclass
class EvalRun:
    """An evaluation run."""
    
    run_id: str
    timestamp: str
    metrics: Dict[str, float]
    cases_passed: int
    cases_failed: int
    duration_seconds: float
    config: Dict[str, Any]


@dataclass
class DegradationAlert:
    """Alert for metric degradation."""
    
    metric: str
    baseline: float
    current: float
    delta: float
    severity: str  # warning, critical


class AutomatedEvalPipeline:
    """Automated evaluation pipeline.
    
    Per RP-370:
    - Daily evaluation runs
    - Automatic metric aggregation
    - Degradation alerts
    """
    
    def __init__(
        self,
        baseline_path: Optional[str] = None,
        output_dir: str = "reports/eval",
        alert_threshold: float = 0.05,
    ):
        self.baseline_path = baseline_path
        self.output_dir = Path(output_dir)
        self.alert_threshold = alert_threshold
        self._baseline: Optional[Dict[str, float]] = None
    
    def load_baseline(self) -> Dict[str, float]:
        """Load baseline metrics."""
        if self._baseline:
            return self._baseline
        
        if self.baseline_path and Path(self.baseline_path).exists():
            with open(self.baseline_path) as f:
                self._baseline = json.load(f)
        else:
            self._baseline = {
                "success_rate": 0.80,
                "claim_precision": 0.70,
                "citation_precision": 0.60,
            }
        
        return self._baseline
    
    def run_evaluation(
        self,
        eval_cases: List[Dict[str, Any]],
        runner=None,
    ) -> EvalRun:
        """Run evaluation on cases.
        
        Args:
            eval_cases: List of evaluation cases.
            runner: Optional custom runner.
            
        Returns:
            EvalRun with results.
        """
        import time
        start = time.time()
        
        results = []
        passed = 0
        failed = 0
        
        for case in eval_cases:
            try:
                result = self._run_case(case, runner)
                results.append(result)
                if result.get("passed"):
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                results.append({"error": str(e), "passed": False})
        
        duration = time.time() - start
        metrics = self._aggregate_metrics(results)
        
        run = EvalRun(
            run_id=f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.utcnow().isoformat() + "Z",
            metrics=metrics,
            cases_passed=passed,
            cases_failed=failed,
            duration_seconds=duration,
            config={},
        )
        
        self._save_run(run)
        
        return run
    
    def _run_case(
        self,
        case: Dict[str, Any],
        runner=None,
    ) -> Dict[str, Any]:
        """Run a single evaluation case."""
        # Placeholder implementation
        return {
            "case_id": case.get("id"),
            "passed": True,
            "metrics": {
                "claim_precision": 0.75,
                "citation_precision": 0.65,
            },
        }
    
    def _aggregate_metrics(
        self,
        results: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Aggregate metrics from results."""
        if not results:
            return {}
        
        metrics = {}
        metric_keys = ["claim_precision", "citation_precision"]
        
        for key in metric_keys:
            values = [r.get("metrics", {}).get(key, 0) for r in results if "metrics" in r]
            if values:
                metrics[key] = sum(values) / len(values)
        
        passed = sum(1 for r in results if r.get("passed"))
        metrics["success_rate"] = passed / len(results) if results else 0
        
        return metrics
    
    def _save_run(self, run: EvalRun) -> None:
        """Save evaluation run."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        run_path = self.output_dir / f"{run.run_id}.json"
        with open(run_path, "w") as f:
            json.dump({
                "run_id": run.run_id,
                "timestamp": run.timestamp,
                "metrics": run.metrics,
                "cases_passed": run.cases_passed,
                "cases_failed": run.cases_failed,
                "duration_seconds": run.duration_seconds,
            }, f, indent=2)
    
    def check_degradation(
        self,
        current_metrics: Dict[str, float],
    ) -> List[DegradationAlert]:
        """Check for metric degradation.
        
        Args:
            current_metrics: Current metrics.
            
        Returns:
            List of degradation alerts.
        """
        baseline = self.load_baseline()
        alerts = []
        
        for metric, baseline_val in baseline.items():
            current_val = current_metrics.get(metric, 0)
            delta = baseline_val - current_val
            
            if delta > self.alert_threshold:
                severity = "critical" if delta > 0.10 else "warning"
                alerts.append(DegradationAlert(
                    metric=metric,
                    baseline=baseline_val,
                    current=current_val,
                    delta=delta,
                    severity=severity,
                ))
        
        return alerts
