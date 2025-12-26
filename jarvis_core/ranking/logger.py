"""
JARVIS Ranking Logger

ランキングログ出力（学習データ収集用）
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import RankingItem


def log_ranking(
    path: str,
    task_id: str,
    stage: str,
    items: List[RankingItem],
    chosen_order: List[str],
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    ランキング結果をログ出力.
    
    後でLightGBMの学習データとして使用可能な形式で保存。
    
    Args:
        path: ログファイルパス
        task_id: タスクID
        stage: ステージ名（planner, retrieval, etc）
        items: ランキングアイテム
        chosen_order: 選択された順序（item_idリスト）
        extra: 追加情報
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "stage": stage,
        "items": [
            {
                "item_id": it.item_id,
                "item_type": it.item_type,
                "features": it.features,
                "metadata": it.metadata,
            }
            for it in items
        ],
        "chosen_order": chosen_order,
        "extra": extra or {},
    }
    
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


class RankingLogger:
    """ランキングロガー."""
    
    def __init__(self, log_path: str = "logs/ranking.jsonl"):
        """
        初期化.
        
        Args:
            log_path: ログファイルパス
        """
        self.log_path = log_path
    
    def log(
        self,
        task_id: str,
        stage: str,
        items: List[RankingItem],
        chosen_order: List[str],
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """ランキングをログ."""
        log_ranking(
            self.log_path,
            task_id,
            stage,
            items,
            chosen_order,
            extra
        )
