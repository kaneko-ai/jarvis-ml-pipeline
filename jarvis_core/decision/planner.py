"""Generate MVP plans and kill criteria for decision options."""
from __future__ import annotations

from typing import Dict, List

from .schema import Option, DISCLAIMER_TEXT


def build_mvp_plan(option: Option) -> Dict[str, List[str]]:
    """Create a 90-day MVP plan for an option."""
    must_learn = ", ".join(option.dependencies.must_learn) or "必須スキルの棚卸し"
    must_access = ", ".join(option.dependencies.must_access) or "主要設備の確認"

    return {
        "disclaimer": DISCLAIMER_TEXT,
        "first_2_weeks": [
            "研究環境のセットアップとルール確認",
            f"最短学習: {must_learn}",
            f"アクセス確認: {must_access}",
        ],
        "day_30": [
            "最小実験または最小データ収集の実施",
            "成功条件を数値で定義しログ化",
        ],
        "day_60": [
            "再現性チェック (再実行/別条件での再現)",
            "解析パイプラインの最小版を確立",
        ],
        "day_90": [
            "成果とリスクの再評価を実施",
            "継続・ピボット・撤退の判断を記録",
        ],
    }


def build_kill_criteria(option: Option) -> List[str]:
    """Create measurable kill criteria for an option."""
    criteria = [
        "8週間以内に主要アウトプットの定量指標が1つも達成できない",
        "主要資源(設備/データ/試薬)の利用可能時間が週10時間未満に低下",
        "指導面談が月1回未満となり方向性レビューが途絶える",
    ]

    if option.dependencies.must_access:
        criteria.append("必須設備の利用予約が連続4週間取得できない")
    if option.dependencies.must_learn:
        criteria.append("必須スキルの習得評価が60日以内に達成できない")

    return criteria
