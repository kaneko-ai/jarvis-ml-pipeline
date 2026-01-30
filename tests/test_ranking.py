"""
JARVIS Ranking Tests
"""

from jarvis_core.ranking import (
    HeuristicRanker,
    RankingItem,
    log_ranking,
)
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest


class TestRankingItem:
    """RankingItem tests."""

    def test_create_item(self):
        """アイテムを作成できること."""
        item = RankingItem(item_id="item1", item_type="paper", features={"relevance": 0.9})
        assert item.item_id == "item1"
        assert item.get_feature("relevance") == 0.9

    def test_get_feature_default(self):
        """存在しない特徴量はデフォルト値を返すこと."""
        item = RankingItem(item_id="item1", item_type="paper")
        assert item.get_feature("missing", 0.5) == 0.5


class TestHeuristicRanker:
    """HeuristicRanker tests."""

    def test_rank_by_relevance(self):
        """relevanceでランキングできること."""
        ranker = HeuristicRanker()

        items = [
            RankingItem("a", "paper", {"relevance": 0.5}),
            RankingItem("b", "paper", {"relevance": 0.9}),
            RankingItem("c", "paper", {"relevance": 0.7}),
        ]

        ranked = ranker.rank(items, {})

        assert ranked[0].item_id == "b"
        assert ranked[1].item_id == "c"
        assert ranked[2].item_id == "a"

    def test_custom_weights(self):
        """カスタム重みでランキングできること."""
        ranker = HeuristicRanker(weights={"priority": 1.0})

        items = [
            RankingItem("a", "task", {"priority": 1}),
            RankingItem("b", "task", {"priority": 3}),
        ]

        ranked = ranker.rank(items, {})
        assert ranked[0].item_id == "b"


class TestRankingLogger:
    """RankingLogger tests."""

    def test_log_ranking(self):
        """ログを出力できること."""
        with TemporaryDirectory() as tmpdir:
            log_path = f"{tmpdir}/ranking.jsonl"

            items = [
                RankingItem("a", "paper", {"relevance": 0.9}),
                RankingItem("b", "paper", {"relevance": 0.5}),
            ]

            log_ranking(log_path, "task1", "retrieval", items, ["a", "b"])

            # ログが書き込まれていること
            log_file = Path(log_path)
            assert log_file.exists()

            with open(log_path) as f:
                record = json.loads(f.readline())

            assert record["task_id"] == "task1"
            assert record["stage"] == "retrieval"
            assert len(record["items"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
