"""Comprehensive tests for visualization module."""

import pytest

from jarvis_core.visualization.advanced import (
    BubbleChartGenerator,
    ForceGraphGenerator,
    SankeyGenerator,
    TreemapGenerator,
    TrendPredictor,
    get_bubble_chart_generator,
    get_force_graph_generator,
    get_sankey_generator,
    get_treemap_generator,
    get_trend_predictor,
)


class TestSankeyGenerator:
    """Test Sankey diagram generator."""

    def test_generate_citation_flow(self):
        papers = [
            {"pmid": "1", "title": "Paper 1", "references": ["2"]},
            {"pmid": "2", "title": "Paper 2", "references": []},
        ]
        sg = SankeyGenerator()
        result = sg.generate_citation_flow(papers)
        assert "nodes" in result
        assert "links" in result
        assert len(result["nodes"]) == 2

    def test_generate_topic_flow(self):
        categories = {"AI": [{"year": 2024}, {"year": 2023}], "Healthcare": [{"year": 2024}]}
        sg = SankeyGenerator()
        result = sg.generate_topic_flow(categories)
        assert len(result["nodes"]) > 0


class TestForceGraphGenerator:
    """Test force graph generator."""

    def test_generate_author_network(self):
        papers = [{"authors": "Smith J, Johnson A"}, {"authors": "Johnson A, Williams B"}]
        fg = ForceGraphGenerator()
        result = fg.generate_author_network(papers)
        assert len(result["nodes"]) == 3
        assert len(result["links"]) >= 1

    def test_generate_citation_network(self):
        papers = [{"pmid": "1", "title": "Test", "citation_count": 10}]
        fg = ForceGraphGenerator()
        result = fg.generate_citation_network(papers)
        assert len(result["nodes"]) == 1


class TestBubbleChartGenerator:
    """Test bubble chart generator."""

    def test_generate_impact_chart(self):
        papers = [{"pmid": "1", "title": "Test", "year": 2024, "citation_count": 50}]
        bg = BubbleChartGenerator()
        result = bg.generate_impact_chart(papers)
        assert len(result) == 1
        assert "x" in result[0]
        assert "y" in result[0]
        assert "r" in result[0]


class TestTreemapGenerator:
    """Test treemap generator."""

    def test_generate_category_treemap(self):
        papers = [{"category": "AI", "subcategory": "ML"}, {"category": "AI", "subcategory": "DL"}]
        tm = TreemapGenerator()
        result = tm.generate_category_treemap(papers)
        assert "name" in result
        assert "children" in result

    def test_generate_journal_treemap(self):
        papers = [{"journal": "Nature"}, {"journal": "Nature"}, {"journal": "Science"}]
        tm = TreemapGenerator()
        result = tm.generate_journal_treemap(papers)
        assert len(result["children"]) == 2


class TestTrendPredictor:
    """Test trend predictor."""

    def test_predict_trend_increasing(self):
        tp = TrendPredictor()
        tp.add_data("AI", 2020, 100)
        tp.add_data("AI", 2021, 150)
        tp.add_data("AI", 2022, 200)
        result = tp.predict_trend("AI")
        assert result["trend"] == "increasing"
        assert "predictions" in result

    def test_predict_trend_decreasing(self):
        tp = TrendPredictor()
        tp.add_data("old_tech", 2020, 200)
        tp.add_data("old_tech", 2021, 150)
        tp.add_data("old_tech", 2022, 100)
        result = tp.predict_trend("old_tech")
        assert result["trend"] == "decreasing"

    def test_get_hot_topics(self):
        tp = TrendPredictor()
        tp.add_data("AI", 2020, 100)
        tp.add_data("AI", 2021, 200)
        tp.add_data("ML", 2020, 50)
        tp.add_data("ML", 2021, 60)
        hot = tp.get_hot_topics(2)
        assert len(hot) <= 2


class TestFactoryFunctions:
    """Test factory functions."""

    def test_get_sankey_generator(self):
        assert isinstance(get_sankey_generator(), SankeyGenerator)

    def test_get_force_graph_generator(self):
        assert isinstance(get_force_graph_generator(), ForceGraphGenerator)

    def test_get_bubble_chart_generator(self):
        assert isinstance(get_bubble_chart_generator(), BubbleChartGenerator)

    def test_get_treemap_generator(self):
        assert isinstance(get_treemap_generator(), TreemapGenerator)

    def test_get_trend_predictor(self):
        assert isinstance(get_trend_predictor(), TrendPredictor)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
