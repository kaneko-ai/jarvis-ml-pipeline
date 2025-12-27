"""External API - 外部公開API設計.

AG-API原則:
- API は"契約の薄皮"
- 判定・Verify・Judgeはすべて内部Coreが行う
- API は run_id と状態を返すだけ

提供API:
- POST /run
- GET /runs/{run_id}
- GET /health
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .sla import SLATier, SLAMonitor, RateLimiter, AbuseDetector

logger = logging.getLogger(__name__)


@dataclass
class APIRequest:
    """APIリクエスト."""
    task_goal: str
    task_category: str = "generic"
    options: Optional[Dict[str, Any]] = None
    api_key: Optional[str] = None


@dataclass
class APIResponse:
    """APIレスポンス."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "data": self.data,
        }
        if self.error:
            result["error"] = self.error
        return result


class ExternalAPIHandler:
    """外部API ハンドラー.
    
    AG-API原則に従い、以下のみを提供:
    - POST /run → run_id を返すだけ
    - GET /runs/{run_id} → status を返すだけ
    - GET /health → ヘルスチェック
    
    禁止:
    - 結果生成API
    - Verify bypass API
    - ログ直接操作API
    """
    
    def __init__(self, tier: SLATier = SLATier.TIER_0):
        self.tier = tier
        self.sla_monitor = SLAMonitor(tier)
        self.rate_limiter = RateLimiter(tier)
        self.abuse_detector = AbuseDetector()
    
    def post_run(self, request: APIRequest) -> APIResponse:
        """POST /run - タスク実行.
        
        処理:
        1. 即時に run_id を発行
        2. 実行は非同期
        
        Returns:
            run_id と初期status
        """
        # SLAメトリクス開始
        metrics = self.sla_monitor.start_request()
        
        # レート制限チェック
        allowed, reason = self.rate_limiter.check_rate_limit()
        if not allowed:
            return APIResponse(
                success=False,
                data={},
                error=reason,
            )
        
        # Abuseチェック
        input_hash = hashlib.md5(request.task_goal.encode()).hexdigest()
        is_abuse, abuse_reason = self.abuse_detector.check_abuse(input_hash)
        if is_abuse:
            return APIResponse(
                success=False,
                data={"status": "blocked"},
                error=abuse_reason,
            )
        
        # run_id発行（実際の実行は非同期）
        from jarvis_core.app import run_task
        import uuid
        
        run_id = str(uuid.uuid4())
        
        # レコード
        self.rate_limiter.record_request()
        self.rate_limiter.record_run()
        self.sla_monitor.record_run_id_issued(metrics)
        
        # SLA違反チェック
        if metrics.sla_violated:
            # 違反時も正常レスポンスは返すが、statusをdegradedに
            return APIResponse(
                success=True,
                data={
                    "run_id": run_id,
                    "status": "degraded",
                    "sla_tier": self.tier.value,
                    "warning": metrics.violation_reason,
                },
            )
        
        return APIResponse(
            success=True,
            data={
                "run_id": run_id,
                "status": "queued",
                "sla_tier": self.tier.value,
            },
        )
    
    def get_run(self, run_id: str) -> APIResponse:
        """GET /runs/{run_id} - 結果取得.
        
        出力（最小）:
        - status
        - gate_passed
        - summary（簡潔）
        
        禁止:
        - 内部ログ全文
        - raw evidence
        """
        from jarvis_core.storage import RunStore
        
        store = RunStore(run_id)
        
        if not store.run_dir.exists():
            return APIResponse(
                success=False,
                data={},
                error=f"Run not found: {run_id}",
            )
        
        result = store.load_result()
        eval_summary = store.load_eval()
        
        if not result:
            return APIResponse(
                success=True,
                data={
                    "run_id": run_id,
                    "status": "running",
                },
            )
        
        # 最小限の情報のみ返す
        response_data = {
            "run_id": run_id,
            "status": result.get("status", "unknown"),
            "gate_passed": eval_summary.get("gate_passed") if eval_summary else None,
        }
        
        # 成功時のみ簡潔なサマリーを追加
        if result.get("status") == "success":
            answer = result.get("answer", "")
            response_data["summary"] = answer[:200] + "..." if len(answer) > 200 else answer
            response_data["citation_count"] = len(result.get("citations", []))
        
        # 失敗時はfail_reasonsを追加
        if result.get("status") == "failed" and eval_summary:
            fail_reasons = eval_summary.get("fail_reasons", [])
            response_data["fail_reasons"] = [
                {"code": r.get("code"), "msg": r.get("msg")}
                for r in fail_reasons[:3]  # 最大3つ
            ]
        
        return APIResponse(
            success=True,
            data=response_data,
        )
    
    def get_health(self) -> APIResponse:
        """GET /health - ヘルスチェック."""
        availability = self.sla_monitor.calculate_availability()
        
        return APIResponse(
            success=True,
            data={
                "status": "healthy",
                "tier": self.tier.value,
                "availability": round(availability, 4),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
