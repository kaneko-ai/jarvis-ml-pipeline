"""Coverage tests for jarvis_core.ranking.explainer."""

from __future__ import annotations

import pytest

from jarvis_core.ranking.explainer import (
    ExplainableRanker,
    RankingExplanation,
    explain_ranking,
)


class TestRankingExplanation:
    def test_to_dict(self) -> None:
        exp = RankingExplanation(
            item_id="p1", rank=1, score=95.0,
            factors={"relevance": 0.9, "evidence": 0.8},
            explanation_text="Top paper",
            contributing_factors=["relevance: 0.90"],
        )
        d = exp.to_dict()
        assert d["item_id"] == "p1"
        assert "relevance" in d["factors"]

    def test_defaults(self) -> None:
        exp = RankingExplanation(item_id="p1", rank=1, score=50.0)
        assert exp.factors == {}
        assert exp.contributing_factors == []


class TestExplainableRanker:
    def test_explain_top_rank(self) -> None:
        ranker = ExplainableRanker()
        exp = ranker.explain("p1", 1, 95.0, {"relevance": 0.9, "evidence": 0.8, "recency": 0.7})
        assert exp.rank == 1
        assert "上位" in exp.explanation_text
        assert len(exp.contributing_factors) == 3

    def test_explain_mid_rank(self) -> None:
        ranker = ExplainableRanker()
        exp = ranker.explain("p5", 5, 70.0, {"relevance": 0.6, "evidence": 0.5})
        assert "上位10以内" in exp.explanation_text

    def test_explain_low_rank(self) -> None:
        ranker = ExplainableRanker()
        exp = ranker.explain("p15", 15, 30.0, {"relevance": 0.3, "evidence": 0.2})
        assert "15位" in exp.explanation_text

    def test_explain_high_main_factor(self) -> None:
        ranker = ExplainableRanker()
        exp = ranker.explain("p1", 1, 95.0, {"relevance": 0.95})
        assert "特に" in exp.explanation_text

    def test_explain_moderate_main_factor(self) -> None:
        ranker = ExplainableRanker()
        exp = ranker.explain("p1", 1, 80.0, {"relevance": 0.65})
        assert "比較的" in exp.explanation_text

    def test_explain_low_factor_improvement(self) -> None:
        ranker = ExplainableRanker()
        exp = ranker.explain("p1", 1, 80.0, {"relevance": 0.9, "recency": 0.2})
        assert "改善" in exp.explanation_text

    def test_explain_no_factors(self) -> None:
        ranker = ExplainableRanker()
        exp = ranker.explain("p1", 1, 50.0, {})
        assert "上位" in exp.explanation_text

    def test_explain_batch(self) -> None:
        ranker = ExplainableRanker()
        items = [
            {"item_id": "p1", "rank": 1, "score": 90, "factors": {"relevance": 0.9}},
            {"item_id": "p2", "rank": 2, "score": 80, "factors": {"relevance": 0.8}},
        ]
        results = ranker.explain_batch(items)
        assert len(results) == 2
        assert results[0].item_id == "p1"

    def test_explain_batch_missing_keys(self) -> None:
        ranker = ExplainableRanker()
        items = [{"data": "no keys"}]
        results = ranker.explain_batch(items)
        assert len(results) == 1
        assert results[0].item_id == ""

    def test_generate_summary_empty(self) -> None:
        ranker = ExplainableRanker()
        assert "ありません" in ranker.generate_summary([])

    def test_generate_summary_normal(self) -> None:
        ranker = ExplainableRanker()
        exps = [
            RankingExplanation(item_id="p1", rank=1, score=90, factors={"relevance": 0.9, "evidence": 0.8},
                              explanation_text="Top"),
            RankingExplanation(item_id="p2", rank=2, score=80, factors={"relevance": 0.7, "evidence": 0.6},
                              explanation_text="Second"),
            RankingExplanation(item_id="p3", rank=3, score=70, factors={"relevance": 0.5, "evidence": 0.4},
                              explanation_text="Third"),
            RankingExplanation(item_id="p4", rank=4, score=60, factors={"relevance": 0.3},
                              explanation_text="Fourth"),
        ]
        summary = ranker.generate_summary(exps)
        assert "ランキングサマリー" in summary
        assert "上位3件" in summary
        assert "全体傾向" in summary

    def test_custom_top_factors(self) -> None:
        ranker = ExplainableRanker(top_factors=1)
        exp = ranker.explain("p1", 1, 90, {"a": 0.9, "b": 0.8, "c": 0.7})
        assert len(exp.contributing_factors) == 1


class TestConvenienceFunction:
    def test_explain_ranking(self) -> None:
        items = [
            {"item_id": "p1", "rank": 1, "score": 90, "factors": {"relevance": 0.9}},
        ]
        results = explain_ranking(items)
        assert len(results) == 1
        assert results[0].rank == 1
