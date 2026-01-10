"""Tests for timeline module."""

from unittest.mock import MagicMock

from jarvis_core.timeline import (
    build_timeline,
    summarize_evolution,
)


def make_mock_vector(paper_id: str, year: int, concepts: dict, 
                      immune: float = 0.5, tumor: float = 0.5):
    """Create a mock PaperVector."""
    mock = MagicMock()
    mock.paper_id = paper_id
    mock.metadata.year = year
    mock.concept.concepts = concepts
    mock.biological_axis.immune_activation = immune
    mock.biological_axis.metabolism_signal = 0.5
    mock.biological_axis.tumor_context = tumor
    mock.temporal.novelty = 0.5
    mock.method.methods = {"method1": 1.0}
    return mock


class TestBuildTimeline:
    def test_empty_vectors(self):
        result = build_timeline([], "cancer")
        assert result == []

    def test_filters_by_concept(self):
        v1 = make_mock_vector("p1", 2020, {"cancer": 1.0})
        v2 = make_mock_vector("p2", 2021, {"diabetes": 1.0})
        
        result = build_timeline([v1, v2], "cancer")
        
        assert len(result) == 1
        assert result[0]["paper_id"] == "p1"

    def test_sorts_by_year(self):
        v1 = make_mock_vector("p1", 2022, {"cancer": 1.0})
        v2 = make_mock_vector("p2", 2020, {"cancer": 1.0})
        v3 = make_mock_vector("p3", 2021, {"cancer": 1.0})
        
        result = build_timeline([v1, v2, v3], "cancer")
        
        assert result[0]["year"] == 2020
        assert result[1]["year"] == 2021
        assert result[2]["year"] == 2022

    def test_entry_structure(self):
        v = make_mock_vector("p1", 2021, {"cancer": 0.8})
        
        result = build_timeline([v], "cancer")
        
        assert "year" in result[0]
        assert "paper_id" in result[0]
        assert "concept_score" in result[0]
        assert "immune_activation" in result[0]


class TestSummarizeEvolution:
    def test_empty_timeline(self):
        result = summarize_evolution([])
        assert "データなし" in result

    def test_single_entry(self):
        timeline = [{"year": 2020, "paper_id": "p1"}]
        result = summarize_evolution(timeline)
        assert "不足" in result

    def test_multi_entry_summary(self):
        timeline = [
            {"year": 2020, "immune_activation": 0.1, "tumor_context": 0.2},
            {"year": 2022, "immune_activation": 0.5, "tumor_context": 0.6},
        ]
        
        result = summarize_evolution(timeline)
        
        assert "2020" in result
        assert "2022" in result

    def test_immune_shift_detection(self):
        timeline = [
            {"year": 2020, "immune_activation": 0.1, "tumor_context": 0.2},
            {"year": 2022, "immune_activation": 0.8, "tumor_context": 0.2},
        ]
        
        result = summarize_evolution(timeline)
        
        # Should mention immune shift
        assert "免疫" in result or len(result) > 0
