#!/usr/bin/env python
"""
JARVIS Phase2 デモスクリプト

10件の判断を自動実行し、DecisionItemを蓄積。
Phase3（自己評価）の成績表が計算可能になる。

使い方:
    python scripts/run_phase2_demo.py
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from jarvis_core.intelligence.goldset_index import GoldsetIndex
from jarvis_core.intelligence.mandatory_search import MandatorySearchJudge
from jarvis_core.intelligence.decision_item import DecisionItem, DecisionStore, DecisionPattern


# デモ用の判断対象（架空のIssue）
DEMO_ISSUES = [
    {
        "id": "demo_001",
        "context": "Retrieverの多層化を導入するか検討",
        "description": "検索精度向上のためRetrieverを階層化する提案",
    },
    {
        "id": "demo_002",
        "context": "最新のGPT-5論文を即座にJavisに統合するか",
        "description": "発表直後のLLM論文、再現コードなし",
    },
    {
        "id": "demo_003",
        "context": "BibTeX自動取得をCrossref APIで実装するか",
        "description": "DOIからメタデータを自動取得、小改修で可能",
    },
    {
        "id": "demo_004",
        "context": "Screenpipe連携を初期段階で導入するか",
        "description": "作業ログの自動取得、セキュリティリスクあり",
    },
    {
        "id": "demo_005",
        "context": "全論文をGPU埋め込みでベクトル化するか",
        "description": "コスト高、運用負荷大",
    },
    {
        "id": "demo_006",
        "context": "評価軸に「再現性」を追加するか",
        "description": "判断精度向上に直結、小改修",
    },
    {
        "id": "demo_007",
        "context": "GraphRAGを今すぐ全面導入するか",
        "description": "Knowledge Graph未整備、時期尚早の可能性",
    },
    {
        "id": "demo_008",
        "context": "週次トレンドレポートの自動生成を導入するか",
        "description": "情報収集効率化、中程度の工数",
    },
    {
        "id": "demo_009",
        "context": "Javisの判断ログをMarkdown形式で出力するか",
        "description": "可読性向上、小改修で可能",
    },
    {
        "id": "demo_010",
        "context": "自己改変機能（自動コード生成）を導入するか",
        "description": "制御不能リスク、Human-in-the-loop原則に反する可能性",
    },
]


def run_demo():
    """デモを実行."""
    print("=" * 60)
    print("JARVIS Phase2 デモ: 類似判断検索の自動実行")
    print("=" * 60)
    print()

    # Goldsetインデックス初期化
    goldset_index = GoldsetIndex()
    print(f"[INFO] Goldset: {len(goldset_index.list_all())} 件ロード済み")

    # DecisionStore初期化
    decision_store = DecisionStore()
    print(f"[INFO] DecisionStore: {len(decision_store.list_all())} 件既存")

    # MandatorySearchJudge初期化
    judge = MandatorySearchJudge(goldset_index=goldset_index)

    print()
    print("-" * 60)
    print("判断を開始します...")
    print("-" * 60)
    print()

    results = []

    for issue in DEMO_ISSUES:
        print(f"\n### Issue: {issue['id']}")
        print(f"Context: {issue['context']}")

        # Phase2判断を実行
        result = judge.judge(
            issue_id=issue["id"],
            issue_context=issue["context"],
            description=issue.get("description", ""),
        )

        # 結果を表示
        print(f"Decision: {result.decision.status.value}")
        if result.similar_search.similar_judgments:
            top_similar = result.similar_search.similar_judgments[0]
            print(f"類似判断: {top_similar.entry.context[:40]}... ({top_similar.similarity:.2f})")

        # DecisionItemとして保存
        decision_item = DecisionItem(
            decision_id=f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{issue['id']}",
            context=issue["context"],
            decision=result.decision.status.value,
            pattern=DecisionPattern.UNCLASSIFIED,  # 後で分類
            reason=result.decision.decision_reason,
        )
        decision_store.add(decision_item)

        results.append(result)

    print()
    print("=" * 60)
    print("デモ完了")
    print("=" * 60)

    # サマリー
    accept_count = sum(1 for r in results if r.decision.status.value == "accept")
    reject_count = sum(1 for r in results if r.decision.status.value == "reject")

    print(
        f"""
結果サマリー:
- 総判断数: {len(results)}
- Accept: {accept_count}
- Reject: {reject_count}
- DecisionStore: {len(decision_store.list_all())} 件

Phase3（自己評価）の条件:
- DecisionItem: {len(decision_store.list_all())} / 20件以上
- 類似判断検索: {len(results)} / 10回以上
"""
    )

    # 判断レポート出力（1件目のみ詳細）
    print()
    print("-" * 60)
    print("判断レポート例（Issue 1）:")
    print("-" * 60)
    print(results[0].format_full_output())

    return results


if __name__ == "__main__":
    run_demo()
