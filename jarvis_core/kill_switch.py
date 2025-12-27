"""Kill Conditions - 途中中断基準.

Kill条件は「健全な設計の一部」。
Killは自動で起きなければ意味がない。

Kill条件カテゴリ:
- KILL-A: 構造破壊 → 即Kill
- KILL-B: 品質劣化 → Phase巻き戻し
- KILL-C: 再現性破壊 → PL2以前に戻し
- KILL-D: 自動化暴走 → 自動停止
- KILL-E: 運用リスク → 商用モード停止
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KillCategory(Enum):
    """Kill条件カテゴリ."""
    KILL_A = "structure_broken"     # 構造破壊
    KILL_B = "quality_degraded"     # 品質劣化
    KILL_C = "reproducibility_lost" # 再現性破壊
    KILL_D = "automation_runaway"   # 自動化暴走
    KILL_E = "operational_risk"     # 運用リスク


class KillSeverity(Enum):
    """Kill深刻度."""
    CRITICAL = "critical"  # 即停止
    HIGH = "high"          # Phase巻き戻し
    MEDIUM = "medium"      # 警告
    LOW = "low"           # ログのみ


@dataclass
class KillCondition:
    """Kill条件の定義."""
    id: str
    category: KillCategory
    severity: KillSeverity
    description: str
    check_function: str  # チェック関数名
    action: str  # 発動時のアクション


@dataclass
class KillEvent:
    """Kill発生イベント."""
    condition_id: str
    category: KillCategory
    severity: KillSeverity
    timestamp: str
    details: Dict[str, Any]
    action_taken: str


# Kill条件定義（固定）
KILL_CONDITIONS: List[KillCondition] = [
    # KILL-A: 構造破壊
    KillCondition(
        id="KILL-A-001",
        category=KillCategory.KILL_A,
        severity=KillSeverity.CRITICAL,
        description="成果物契約が1つでも欠損",
        check_function="check_artifact_contract",
        action="immediate_stop",
    ),
    KillCondition(
        id="KILL-A-002",
        category=KillCategory.KILL_A,
        severity=KillSeverity.CRITICAL,
        description="spec_lintが通らない",
        check_function="check_spec_lint",
        action="immediate_stop",
    ),
    
    # KILL-B: 品質劣化
    KillCondition(
        id="KILL-B-001",
        category=KillCategory.KILL_B,
        severity=KillSeverity.HIGH,
        description="citation無しsuccessが1回でも発生",
        check_function="check_no_citation_success",
        action="phase_rollback",
    ),
    KillCondition(
        id="KILL-B-002",
        category=KillCategory.KILL_B,
        severity=KillSeverity.HIGH,
        description="gate_passed=false successが発生",
        check_function="check_gate_fail_success",
        action="phase_rollback",
    ),
    
    # KILL-C: 再現性破壊
    KillCondition(
        id="KILL-C-001",
        category=KillCategory.KILL_C,
        severity=KillSeverity.HIGH,
        description="同一入力で構造差分が発生",
        check_function="check_structure_diff",
        action="rollback_to_pl2",
    ),
    
    # KILL-D: 自動化暴走
    KillCondition(
        id="KILL-D-001",
        category=KillCategory.KILL_D,
        severity=KillSeverity.HIGH,
        description="retry回数上限超過",
        check_function="check_retry_limit",
        action="auto_stop",
    ),
    KillCondition(
        id="KILL-D-002",
        category=KillCategory.KILL_D,
        severity=KillSeverity.MEDIUM,
        description="同一fail_reason連続発生",
        check_function="check_repeated_failures",
        action="auto_stop",
    ),
    
    # KILL-E: 運用リスク
    KillCondition(
        id="KILL-E-001",
        category=KillCategory.KILL_E,
        severity=KillSeverity.HIGH,
        description="コスト上限超過",
        check_function="check_cost_limit",
        action="commercial_stop",
    ),
    KillCondition(
        id="KILL-E-002",
        category=KillCategory.KILL_E,
        severity=KillSeverity.HIGH,
        description="レイテンシSLA超過",
        check_function="check_latency_sla",
        action="commercial_stop",
    ),
]


class KillSwitch:
    """Kill Switch - Kill条件の監視と発動."""
    
    def __init__(self, incidents_file: str = "docs/INCIDENTS.md"):
        self.incidents_file = Path(incidents_file)
        self.events: List[KillEvent] = []
        self._killed = False
        self._kill_reason: Optional[str] = None
    
    @property
    def is_killed(self) -> bool:
        """Killされているか."""
        return self._killed
    
    @property
    def kill_reason(self) -> Optional[str]:
        """Kill理由."""
        return self._kill_reason
    
    def check_artifact_contract(self, run_dir: Path) -> bool:
        """成果物契約をチェック.
        
        Returns:
            違反があればTrue（Kill条件成立）
        """
        from jarvis_core.storage import RunStore
        
        if not run_dir.exists():
            return False
        
        store = RunStore(run_dir.name, base_dir=str(run_dir.parent))
        missing = store.validate_contract()
        return len(missing) > 0
    
    def check_no_citation_success(self, result: Dict[str, Any]) -> bool:
        """citation無しsuccessをチェック.
        
        Returns:
            違反があればTrue
        """
        if result.get("status") == "success":
            citations = result.get("citations", [])
            return len(citations) == 0
        return False
    
    def check_gate_fail_success(
        self,
        result: Dict[str, Any],
        eval_summary: Dict[str, Any],
    ) -> bool:
        """gate_passed=false successをチェック.
        
        Returns:
            違反があればTrue
        """
        if result.get("status") == "success":
            return not eval_summary.get("gate_passed", True)
        return False
    
    def check_retry_limit(self, retry_count: int, max_retries: int = 3) -> bool:
        """retry上限をチェック.
        
        Returns:
            超過していればTrue
        """
        return retry_count > max_retries
    
    def trigger_kill(
        self,
        condition: KillCondition,
        details: Dict[str, Any],
    ) -> KillEvent:
        """Killを発動.
        
        Args:
            condition: 発動したKill条件
            details: 詳細情報
        
        Returns:
            KillEvent
        """
        event = KillEvent(
            condition_id=condition.id,
            category=condition.category,
            severity=condition.severity,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details,
            action_taken=condition.action,
        )
        
        self.events.append(event)
        
        if condition.severity == KillSeverity.CRITICAL:
            self._killed = True
            self._kill_reason = f"{condition.id}: {condition.description}"
        
        # INCIDENTSに記録
        self._record_incident(event)
        
        logger.warning(
            f"KILL triggered: {condition.id} - {condition.description} "
            f"(action: {condition.action})"
        )
        
        return event
    
    def _record_incident(self, event: KillEvent) -> None:
        """INCIDENTSに記録."""
        if not self.incidents_file.parent.exists():
            self.incidents_file.parent.mkdir(parents=True, exist_ok=True)
        
        entry = f"""
### {event.condition_id} - {event.timestamp}

- **Category**: {event.category.value}
- **Severity**: {event.severity.value}
- **Action**: {event.action_taken}
- **Details**: {event.details}

---
"""
        
        if self.incidents_file.exists():
            content = self.incidents_file.read_text(encoding="utf-8")
        else:
            content = "# JARVIS Incidents Log\n\nKill条件発動の記録。\n\n---\n"
        
        content += entry
        self.incidents_file.write_text(content, encoding="utf-8")
    
    def get_condition_by_id(self, condition_id: str) -> Optional[KillCondition]:
        """IDでKill条件を取得."""
        for cond in KILL_CONDITIONS:
            if cond.id == condition_id:
                return cond
        return None


# =============================================================================
# Legacy API: recommend_kill_switch (Ψ-7)
# Per Ψ-7, this recommends when to stop research based on vector analysis.
# =============================================================================

def recommend_kill_switch(
    theme: str,
    vectors: List[Any],
    months_invested: int = 12,
) -> Dict[str, Any]:
    """研究継続・中止の推奨を判定（Ψ-7）.
    
    Args:
        theme: 研究テーマ
        vectors: PaperVectorのリスト
        months_invested: 投資した月数
    
    Returns:
        推奨結果（recommendation: continue/pivot/stop）
    """
    if not vectors:
        return {
            "theme": theme,
            "recommendation": "stop",
            "stop_score": 1.0,
            "evidence": ["中止根拠なし"],
            "months_invested": months_invested,
            "estimated": True,
        }
    
    # 簡易スコア計算（ベクトルの特性から判定）
    novelty_sum = 0.0
    impact_sum = 0.0
    
    for v in vectors:
        if hasattr(v, "temporal") and hasattr(v.temporal, "novelty"):
            novelty_sum += v.temporal.novelty
        if hasattr(v, "impact") and hasattr(v.impact, "future_potential"):
            impact_sum += v.impact.future_potential
    
    avg_novelty = novelty_sum / len(vectors) if vectors else 0.0
    avg_impact = impact_sum / len(vectors) if vectors else 0.0
    
    # 継続スコア = 新規性 × 将来性
    continue_score = (avg_novelty + avg_impact) / 2
    stop_score = 1 - continue_score
    
    # 判定
    if continue_score >= 0.6:
        recommendation = "continue"
        evidence = [
            f"高い新規性 ({avg_novelty:.2f})",
            f"高い将来性 ({avg_impact:.2f})",
        ]
    elif continue_score >= 0.3:
        recommendation = "pivot"
        evidence = [
            f"中程度の新規性 ({avg_novelty:.2f})",
            "方向修正を検討",
        ]
    else:
        recommendation = "stop"
        evidence = [
            f"低い新規性 ({avg_novelty:.2f})",
            f"低い将来性 ({avg_impact:.2f})",
        ]
    
    return {
        "theme": theme,
        "recommendation": recommendation,
        "stop_score": stop_score,
        "continue_score": continue_score,
        "evidence": evidence,
        "months_invested": months_invested,
        "estimated": True,
    }


def assess_field_evolution(
    vectors: List[Any],
    field_name: str = "unknown",
) -> Dict[str, Any]:
    """分野の進化度を評価（Ψ-7補助）.
    
    Args:
        vectors: PaperVectorのリスト
        field_name: 分野名
    
    Returns:
        評価結果
    """
    if not vectors:
        return {
            "field": field_name,
            "evolution_index": 0.0,
            "trend": "stagnant",
            "estimated": True,
        }
    
    # 年代分布から進化度を推定
    years = []
    for v in vectors:
        if hasattr(v, "metadata") and hasattr(v.metadata, "year"):
            years.append(v.metadata.year)
    
    if not years:
        return {
            "field": field_name,
            "evolution_index": 0.5,
            "trend": "unknown",
            "estimated": True,
        }
    
    # 最近の論文が多いほど進化中
    recent_count = sum(1 for y in years if y >= 2020)
    evolution_index = recent_count / len(years)
    
    if evolution_index >= 0.7:
        trend = "rapidly_evolving"
    elif evolution_index >= 0.4:
        trend = "evolving"
    else:
        trend = "mature"
    
    return {
        "field": field_name,
        "evolution_index": evolution_index,
        "trend": trend,
        "estimated": True,
    }

