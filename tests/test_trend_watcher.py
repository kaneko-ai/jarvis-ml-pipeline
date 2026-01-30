"""Tests for trend watcher module."""

import json
from unittest.mock import MagicMock

import pytest
from jarvis_core.trend.watcher import TrendReport, TrendWatcher
from jarvis_core.trend.sources.base import TrendItem, TrendSource
from jarvis_core.trend.ranker import RankScore


class MockSource(TrendSource):
    """Mock trend source for testing."""

    def __init__(self, name="mock", items=None):
        self._name = name
        self.items = items or []

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return True

    def fetch(self, queries, max_results=10):
        return self.items


class TestTrendReport:
    def test_to_markdown(self):
        item = TrendItem(
            id="1",
            title="Test Trend",
            source="mock",
            url="http://test",
            abstract="Abstract",
            published_date="2024-01-01",
        )
        score = RankScore(novelty=0.8, relevance=1.0)
        report = TrendReport(
            report_id="test_report",
            generated_at="2024-01-01",
            period_start="2023-12-25",
            period_end="2024-01-01",
            items=[item],
            ranked_items=[(item, score)],
            issues=[{"title": "Test Issue", "description": "Desc"}],
        )

        md = report.to_markdown()
        assert "# Trend Report: test_report" in md
        assert "Test Trend" in md
        assert "**Score**: 0.66" in md
        assert "Test Issue" in md

    def test_save(self, tmp_path):
        report = TrendReport(
            report_id="test_report",
            generated_at="2024-01-01",
            period_start="2023-12-25",
            period_end="2024-01-01",
        )
        path = report.save(str(tmp_path))

        assert path.exists()
        assert (tmp_path / "test_report.json").exists()

        data = json.loads((tmp_path / "test_report.json").read_text(encoding="utf-8"))
        assert data["report_id"] == "test_report"


class TestTrendWatcher:
    @pytest.fixture
    def watcher(self):
        return TrendWatcher()

    def test_add_source(self, watcher):
        source = MockSource()
        watcher.add_source(source)
        assert len(watcher.sources) == 1
        assert watcher.sources[0] == source

    def test_collect(self, watcher):
        item1 = TrendItem(
            id="1", title="T1", source="s1", url="u1", abstract="a1", published_date="d1"
        )
        item2 = TrendItem(
            id="2", title="T2", source="s2", url="u2", abstract="a2", published_date="d2"
        )
        # Duplicate item
        item3 = TrendItem(
            id="1", title="T1", source="s1", url="u1", abstract="a1", published_date="d1"
        )

        source = MockSource(items=[item1, item2, item3])
        watcher.add_source(source)

        items = watcher.collect(["query"])

        assert len(items) == 2  # Unique items
        ids = [i.id for i in items]
        assert "1" in ids
        assert "2" in ids

    def test_collect_error_handling(self, watcher):
        source = MagicMock()
        source.fetch.side_effect = Exception("Fetch error")
        source.name = "fail_source"
        watcher.add_source(source)

        items = watcher.collect(["query"])
        assert items == []  # Should handle error gracefully

    def test_generate_report(self, watcher):
        item = TrendItem(
            id="1", title="T1", source="s1", url="u1", abstract="a1", published_date="d1"
        )

        # Mock ranker
        watcher.ranker = MagicMock()
        score = RankScore(novelty=0.8, relevance=1.0)
        watcher.ranker.rank.return_value = [(item, score)]

        report = watcher.generate_report([item], "start", "end")

        assert report.period_start == "start"
        assert len(report.items) == 1
        assert len(report.ranked_items) == 1
        assert len(report.issues) == 1  # Relevance 1.0 > 0.7, so issue generated
        assert report.issues[0]["item_id"] == "1"

    def test_generate_issues(self, watcher):
        item = TrendItem(
            id="1", title="T1", source="s1", url="u1", abstract="a1", published_date="d1"
        )

        # High relevance
        score1 = RankScore(novelty=0.5, relevance=0.8)
        # Low relevance
        score2 = RankScore(novelty=0.5, relevance=0.5)

        items = [(item, score1), (item, score2)]

        issues = watcher._generate_issues(items)
        assert len(issues) == 1
        assert issues[0]["description"].startswith("High relevance")
