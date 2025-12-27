"""
JARVIS Metrics Collector

Phase 3: 判断成績表
- accept_success_rate
- reject_correct_rate
- regret_rate
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .decision_item import DecisionStore
from .outcome_tracker import OutcomeTracker, OutcomeStatus

logger = logging.getLogger(__name__)


@dataclass
class JudgmentMetrics:
    """判断成績表.
    
    月次でJavisの判断精度を数値化。
    """
    period: str                    # 期間（例：2024-01）
    total_decisions: int           # 総判断数
    accept_count: int              # Accept数
    reject_count: int              # Reject数
    
    # Accept系指標
    accept_success_rate: float     # 採用して成功した率
    accept_failure_rate: float     # 採用して失敗した率
    
    # Reject系指標
    reject_correct_rate: float     # 捨てて正解だった率
    
    # 後悔指標
    regret_rate: float             # 後悔率（採用すべきでなかった + 捨てるべきでなかった）
    
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換."""
        return asdict(self)
    
    def to_markdown(self) -> str:
        """Markdown形式で出力."""
        return f"""# 判断成績表: {self.period}

| 指標 | 値 |
|------|-----|
| 総判断数 | {self.total_decisions} |
| Accept数 | {self.accept_count} |
| Reject数 | {self.reject_count} |
| **Accept成功率** | {self.accept_success_rate:.1%} |
| Accept失敗率 | {self.accept_failure_rate:.1%} |
| Reject正答率 | {self.reject_correct_rate:.1%} |
| **後悔率** | {self.regret_rate:.1%} |

生成日時: {self.generated_at}
"""


class MetricsCollector:
    """成績表収集器.
    
    月次で判断の成績表を生成。
    """
    
    def __init__(
        self,
        storage_path: str = "data/metrics",
        decision_store: Optional[DecisionStore] = None,
        outcome_tracker: Optional[OutcomeTracker] = None
    ):
        """
        初期化.
        
        Args:
            storage_path: ストレージパス
            decision_store: DecisionStore
            outcome_tracker: OutcomeTracker
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.decision_store = decision_store or DecisionStore()
        self.outcome_tracker = outcome_tracker or OutcomeTracker()
    
    def collect(self, period: Optional[str] = None) -> JudgmentMetrics:
        """
        成績表を収集.
        
        Args:
            period: 期間（省略時は今月）
        
        Returns:
            JudgmentMetrics
        """
        if period is None:
            period = datetime.now().strftime("%Y-%m")
        
        decisions = self.decision_store.list_all()
        outcomes = self.outcome_tracker._outcomes
        
        # 期間でフィルタ
        period_decisions = [
            d for d in decisions
            if d.timestamp.startswith(period)
        ]
        
        total = len(period_decisions)
        accept_count = len([d for d in period_decisions if d.decision == "accept"])
        reject_count = len([d for d in period_decisions if d.decision == "reject"])
        
        # Outcome集計
        outcome_map = {o.decision_id: o for o in outcomes}
        
        accept_success = 0
        accept_failure = 0
        reject_correct = 0
        regret = 0
        
        for d in period_decisions:
            outcome = outcome_map.get(d.decision_id)
            if not outcome:
                continue
            
            if d.decision == "accept":
                if outcome.status == OutcomeStatus.SUCCESS:
                    accept_success += 1
                elif outcome.status == OutcomeStatus.FAILURE:
                    accept_failure += 1
                    regret += 1
            else:  # reject
                if outcome.status == OutcomeStatus.SUCCESS:
                    # 捨てて正解
                    reject_correct += 1
                elif outcome.status == OutcomeStatus.FAILURE:
                    # 捨てるべきでなかった
                    regret += 1
        
        # 率計算
        accept_success_rate = accept_success / accept_count if accept_count > 0 else 0.0
        accept_failure_rate = accept_failure / accept_count if accept_count > 0 else 0.0
        reject_correct_rate = reject_correct / reject_count if reject_count > 0 else 0.0
        regret_rate = regret / total if total > 0 else 0.0
        
        metrics = JudgmentMetrics(
            period=period,
            total_decisions=total,
            accept_count=accept_count,
            reject_count=reject_count,
            accept_success_rate=accept_success_rate,
            accept_failure_rate=accept_failure_rate,
            reject_correct_rate=reject_correct_rate,
            regret_rate=regret_rate,
        )
        
        # 保存
        self._save(metrics)
        
        logger.info(f"Collected metrics for {period}: success_rate={accept_success_rate:.1%}")
        return metrics
    
    def _save(self, metrics: JudgmentMetrics) -> None:
        """成績表を保存."""
        # JSON
        json_path = self.storage_path / f"metrics_{metrics.period}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metrics.to_dict(), f, ensure_ascii=False, indent=2)
        
        # Markdown
        md_path = self.storage_path / f"metrics_{metrics.period}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(metrics.to_markdown())
    
    def load_history(self, months: int = 6) -> List[JudgmentMetrics]:
        """過去の成績表を読み込み."""
        metrics_files = sorted(self.storage_path.glob("metrics_*.json"))[-months:]
        
        history = []
        for f in metrics_files:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                history.append(JudgmentMetrics(**data))
        
        return history
