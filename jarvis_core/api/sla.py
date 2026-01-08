"""SLA Tiers - 商用SLA定義.

SLA-Tier 0 (Internal/Research): best-effort
SLA-Tier 1 (Public/Free): 99.0% availability
SLA-Tier 2 (Commercial): 99.9% availability
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SLATier(Enum):
    """SLAティア."""

    TIER_0 = "internal"  # Internal/Research
    TIER_1 = "public"  # Public/Free
    TIER_2 = "commercial"  # Commercial


@dataclass
class SLADefinition:
    """SLA定義."""

    tier: SLATier
    availability_target: float  # 0.0 - 1.0
    p95_latency_ms: int  # run受付までのP95レイテンシ
    completion_guarantee: str  # 完走保証レベル
    retry_limit: int  # 最大リトライ回数


# SLA定義（固定）
SLA_DEFINITIONS: dict[SLATier, SLADefinition] = {
    SLATier.TIER_0: SLADefinition(
        tier=SLATier.TIER_0,
        availability_target=0.0,  # best-effort
        p95_latency_ms=0,  # 制限なし
        completion_guarantee="none",
        retry_limit=100,
    ),
    SLATier.TIER_1: SLADefinition(
        tier=SLATier.TIER_1,
        availability_target=0.99,  # 99.0%
        p95_latency_ms=30000,  # 30秒
        completion_guarantee="run_id_only",
        retry_limit=3,
    ),
    SLATier.TIER_2: SLADefinition(
        tier=SLATier.TIER_2,
        availability_target=0.999,  # 99.9%
        p95_latency_ms=5000,  # 5秒
        completion_guarantee="run_id_and_status",
        retry_limit=5,
    ),
}


@dataclass
class SLAMetrics:
    """SLAメトリクス."""

    request_received_at: str
    run_id_issued_at: str | None = None
    status_updated_at: str | None = None
    latency_ms: int | None = None
    sla_violated: bool = False
    violation_reason: str | None = None


class SLAMonitor:
    """SLAモニター."""

    def __init__(self, tier: SLATier = SLATier.TIER_0):
        self.tier = tier
        self.sla_def = SLA_DEFINITIONS[tier]
        self.metrics_history: list[SLAMetrics] = []

    def start_request(self) -> SLAMetrics:
        """リクエスト開始を記録."""
        metrics = SLAMetrics(
            request_received_at=datetime.now(timezone.utc).isoformat(),
        )
        return metrics

    def record_run_id_issued(self, metrics: SLAMetrics) -> None:
        """run_id発行を記録."""
        now = datetime.now(timezone.utc)
        metrics.run_id_issued_at = now.isoformat()

        # レイテンシ計算
        received = datetime.fromisoformat(metrics.request_received_at.replace("Z", "+00:00"))
        latency_ms = int((now - received).total_seconds() * 1000)
        metrics.latency_ms = latency_ms

        # SLA違反チェック
        if self.sla_def.p95_latency_ms > 0 and latency_ms > self.sla_def.p95_latency_ms:
            metrics.sla_violated = True
            metrics.violation_reason = (
                f"Latency {latency_ms}ms exceeds SLA {self.sla_def.p95_latency_ms}ms"
            )
            logger.warning(f"SLA violation: {metrics.violation_reason}")

    def record_status_updated(self, metrics: SLAMetrics) -> None:
        """ステータス更新を記録."""
        metrics.status_updated_at = datetime.now(timezone.utc).isoformat()
        self.metrics_history.append(metrics)

    def get_violation_response(self, metrics: SLAMetrics) -> dict[str, Any]:
        """SLA違反時のレスポンスを生成."""
        return {
            "status": "degraded",
            "sla_tier": self.tier.value,
            "violation": {
                "reason": metrics.violation_reason,
                "latency_ms": metrics.latency_ms,
            },
            "message": "Service is operating with degraded performance",
        }

    def calculate_availability(self) -> float:
        """可用性を計算."""
        if not self.metrics_history:
            return 1.0

        violations = sum(1 for m in self.metrics_history if m.sla_violated)
        return 1.0 - (violations / len(self.metrics_history))


@dataclass
class RateLimitConfig:
    """レート制限設定."""

    requests_per_minute: int
    runs_per_day: int
    retry_limit: int


# ティア別レート制限（固定）
RATE_LIMITS: dict[SLATier, RateLimitConfig] = {
    SLATier.TIER_0: RateLimitConfig(
        requests_per_minute=1000,
        runs_per_day=10000,
        retry_limit=100,
    ),
    SLATier.TIER_1: RateLimitConfig(
        requests_per_minute=5,
        runs_per_day=20,
        retry_limit=1,
    ),
    SLATier.TIER_2: RateLimitConfig(
        requests_per_minute=60,
        runs_per_day=1000,
        retry_limit=5,
    ),
}


class RateLimiter:
    """レートリミッター."""

    def __init__(self, tier: SLATier = SLATier.TIER_0):
        self.tier = tier
        self.config = RATE_LIMITS[tier]
        self._minute_requests: list[datetime] = []
        self._day_runs: list[datetime] = []

    def check_rate_limit(self) -> tuple[bool, str | None]:
        """レート制限をチェック.

        Returns:
            (許可されるか, 拒否理由)
        """
        now = datetime.now(timezone.utc)

        # 1分あたりのリクエスト数チェック
        minute_ago = now.timestamp() - 60
        self._minute_requests = [t for t in self._minute_requests if t.timestamp() > minute_ago]

        if len(self._minute_requests) >= self.config.requests_per_minute:
            return False, f"Rate limit exceeded: {self.config.requests_per_minute} req/min"

        # 1日あたりのrun数チェック
        day_ago = now.timestamp() - 86400
        self._day_runs = [t for t in self._day_runs if t.timestamp() > day_ago]

        if len(self._day_runs) >= self.config.runs_per_day:
            return False, f"Daily limit exceeded: {self.config.runs_per_day} runs/day"

        return True, None

    def record_request(self) -> None:
        """リクエストを記録."""
        self._minute_requests.append(datetime.now(timezone.utc))

    def record_run(self) -> None:
        """runを記録."""
        self._day_runs.append(datetime.now(timezone.utc))


class AbuseDetector:
    """Abuse検知."""

    def __init__(self):
        self._recent_inputs: list[tuple[str, datetime]] = []
        self._fail_counts: dict[str, int] = {}

    def check_abuse(
        self,
        input_hash: str,
        is_failed: bool = False,
    ) -> tuple[bool, str | None]:
        """Abuseをチェック.

        Returns:
            (Abuseか, 理由)
        """
        now = datetime.now(timezone.utc)

        # 同一入力の高速連続実行チェック
        recent_same = [
            t for h, t in self._recent_inputs if h == input_hash and (now - t).total_seconds() < 10
        ]

        if len(recent_same) >= 3:
            return True, "Same input submitted too frequently"

        # failed runの異常連打チェック
        if is_failed:
            self._fail_counts[input_hash] = self._fail_counts.get(input_hash, 0) + 1
            if self._fail_counts[input_hash] >= 5:
                return True, "Too many failed runs for same input"

        # 記録
        self._recent_inputs.append((input_hash, now))
        # 古いエントリを削除
        self._recent_inputs = [
            (h, t) for h, t in self._recent_inputs if (now - t).total_seconds() < 60
        ]

        return False, None
