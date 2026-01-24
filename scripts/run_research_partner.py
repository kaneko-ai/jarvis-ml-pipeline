#!/usr/bin/env python
"""
JARVIS Research Partner Mode デモ

Phase4-7 統合版: 研究パートナーAI

使い方:
    python scripts/run_research_partner.py "研究テーマ"

例:
    python scripts/run_research_partner.py "免疫療法 × LLM活用"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from jarvis_core.intelligence.research_partner import ResearchPartner


def main():
    """メイン."""
    # 引数からテーマを取得
    if len(sys.argv) > 1:
        theme = " ".join(sys.argv[1:])
    else:
        theme = "大規模言語モデルの評価手法"

    print("=" * 60)
    print("JARVIS Research Partner Mode")
    print("=" * 60)
    print()
    print(f"Theme: {theme}")
    print()

    # Research Partner初期化
    partner = ResearchPartner()

    # 相談実行
    result = partner.consult(
        theme=theme,
        constraints="時間制約あり（1週間）",
        current_situation="論文が多すぎて優先順位が不明",
    )

    # 結果出力
    print(result.to_markdown())

    # 最終チェック
    print("-" * 60)
    print("【最終チェック】")
    print(f"✓ 捨てる対象を提示したか: {len(result.action_plan.ignore_items) > 0}")
    print(f"✓ 過去判断と接続: {len(result.past_decisions) > 0}")
    print(f"✓ 次の行動が明確か: {len(result.action_plan.read_items) > 0}")
    print("-" * 60)


if __name__ == "__main__":
    main()
