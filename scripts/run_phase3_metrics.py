#!/usr/bin/env python
"""
JARVIS Phase3 成績表生成スクリプト

DecisionItemとOutcomeから判断成績表を生成。

使い方:
    python scripts/run_phase3_metrics.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from jarvis_core.intelligence.decision_item import DecisionStore
from jarvis_core.intelligence.outcome_tracker import OutcomeTracker, OutcomeRecord, OutcomeStatus
from jarvis_core.intelligence.metrics_collector import MetricsCollector


def run_phase3():
    """Phase3成績表を生成."""
    print("=" * 60)
    print("JARVIS Phase3: 判断成績表の生成")
    print("=" * 60)
    print()

    # DecisionStore読み込み
    decision_store = DecisionStore()
    decisions = decision_store.list_all()
    print(f"[INFO] DecisionStore: {len(decisions)} 件")

    # OutcomeTracker初期化
    outcome_tracker = OutcomeTracker(decision_store=decision_store)

    # デモ用: 一部のDecisionにOutcomeを付与
    print("\n[INFO] デモ用Outcome付与...")
    for i, d in enumerate(decisions[:10]):
        if not d.outcome_status:
            # 偶数はsuccess、奇数の一部はfailure
            if i % 3 == 0:
                status = OutcomeStatus.SUCCESS
                effect = "効果あり"
            elif i % 3 == 1:
                status = OutcomeStatus.NEUTRAL
                effect = "影響なし"
            else:
                status = OutcomeStatus.FAILURE
                effect = "期待外れ"

            record = OutcomeRecord(
                decision_id=d.decision_id,
                status=status,
                effect_description=effect,
                cost_justified=(status == OutcomeStatus.SUCCESS),
                would_repeat=(status != OutcomeStatus.FAILURE),
            )
            outcome_tracker.record(record)

    # MetricsCollector
    print("\n[INFO] 成績表を生成中...")
    metrics_collector = MetricsCollector(
        decision_store=decision_store,
        outcome_tracker=outcome_tracker,
    )

    # 今月の成績表
    metrics = metrics_collector.collect()

    print()
    print("-" * 60)
    print("判断成績表")
    print("-" * 60)
    print(metrics.to_markdown())

    # Outcomeサマリー
    outcome_summary = outcome_tracker.summarize()
    print("-" * 60)
    print("Outcomeサマリー")
    print("-" * 60)
    print(f"- 総件数: {outcome_summary['total']}")
    print(f"- Success: {outcome_summary['success']}")
    print(f"- Neutral: {outcome_summary['neutral']}")
    print(f"- Failure: {outcome_summary['failure']}")
    print(f"- Success Rate: {outcome_summary['success_rate']:.1%}")

    print()
    print("=" * 60)
    print("Phase3 完了")
    print("=" * 60)

    return metrics


if __name__ == "__main__":
    run_phase3()
