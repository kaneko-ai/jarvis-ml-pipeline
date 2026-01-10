"""Tests for visualization.advanced module."""

from jarvis_core.visualization.advanced import (
    SankeyGenerator,
    ForceGraphGenerator,
    BubbleChartGenerator,
    TreemapGenerator,
    TrendPredictor,
)


class TestSankeyGenerator:
    def test_generate_citation_flow_empty(self):
        gen = SankeyGenerator()
        result = gen.generate_citation_flow([])
        
        assert result["nodes"] == []
        assert result["links"] == []

    def test_generate_citation_flow(self):
        gen = SankeyGenerator()
        papers = [
            {"id": "p1", "title": "Paper 1", "citations": ["p2"]},
            {"id": "p2", "title": "Paper 2", "citations": []},
        ]
        
        result = gen.generate_citation_flow(papers)
        
        assert "nodes" in result
        assert "links" in result

    def test_generate_topic_flow_empty(self):
        gen = SankeyGenerator()
        result = gen.generate_topic_flow({})
        
        assert "nodes" in result
        assert "links" in result


class TestForceGraphGenerator:
    def test_generate_author_network_empty(self):
        gen = ForceGraphGenerator()
        result = gen.generate_author_network([])
        
        assert result["nodes"] == []
        assert result["links"] == []

    def test_generate_author_network(self):
        gen = ForceGraphGenerator()
        # Authors should be a comma-separated string per the implementation
        papers = [
            {"id": "p1", "authors": "Alice, Bob"},
            {"id": "p2", "authors": "Bob, Charlie"},
        ]
        
        result = gen.generate_author_network(papers)
        
        assert len(result["nodes"]) > 0

    def test_generate_citation_network(self):
        gen = ForceGraphGenerator()
        papers = [
            {"id": "p1", "title": "Paper 1", "citations": ["p2"]},
            {"id": "p2", "title": "Paper 2", "citations": []},
        ]
        
        result = gen.generate_citation_network(papers)
        
        assert "nodes" in result
        assert "links" in result


class TestBubbleChartGenerator:
    def test_generate_impact_chart_empty(self):
        gen = BubbleChartGenerator()
        result = gen.generate_impact_chart([])
        
        assert result == []

    def test_generate_impact_chart(self):
        gen = BubbleChartGenerator()
        papers = [
            {"id": "p1", "title": "Paper 1", "citations": 10, "year": 2020},
            {"id": "p2", "title": "Paper 2", "citations": 50, "year": 2021},
        ]
        
        result = gen.generate_impact_chart(papers)
        
        assert len(result) == 2
        assert "x" in result[0]
        assert "y" in result[0]
        # "r" is the radius field, not "size"
        assert "r" in result[0]

    def test_generate_author_impact(self):
        gen = BubbleChartGenerator()
        authors = [
            {"name": "Alice", "papers": 5, "citations": 100},
            {"name": "Bob", "papers": 10, "citations": 50},
        ]
        
        result = gen.generate_author_impact(authors)
        
        assert len(result) == 2


class TestTreemapGenerator:
    def test_generate_category_treemap_empty(self):
        gen = TreemapGenerator()
        result = gen.generate_category_treemap([])
        
        # Actual name is "Research Topics"
        assert "Research" in result["name"]
        assert result["children"] == []

    def test_generate_category_treemap(self):
        gen = TreemapGenerator()
        papers = [
            {"id": "p1", "category": "Cancer"},
            {"id": "p2", "category": "Cancer"},
            {"id": "p3", "category": "Immunology"},
        ]
        
        result = gen.generate_category_treemap(papers)
        
        assert len(result["children"]) == 2

    def test_generate_journal_treemap(self):
        gen = TreemapGenerator()
        papers = [
            {"id": "p1", "journal": "Nature"},
            {"id": "p2", "journal": "Science"},
            {"id": "p3", "journal": "Nature"},
        ]
        
        result = gen.generate_journal_treemap(papers)
        
        assert len(result["children"]) == 2


class TestTrendPredictor:
    def test_init(self):
        predictor = TrendPredictor()
        assert predictor.historical_data == {}

    def test_add_data(self):
        predictor = TrendPredictor()
        predictor.add_data("cancer", 2020, 100)
        predictor.add_data("cancer", 2021, 150)
        
        assert "cancer" in predictor.historical_data
        assert len(predictor.historical_data["cancer"]) == 2

    def test_predict_trend(self):
        predictor = TrendPredictor()
        predictor.add_data("cancer", 2020, 100)
        predictor.add_data("cancer", 2021, 150)
        predictor.add_data("cancer", 2022, 200)
        
        result = predictor.predict_trend("cancer", 2025)
        
        assert "topic" in result
        assert "predictions" in result

    def test_get_hot_topics(self):
        predictor = TrendPredictor()
        predictor.add_data("cancer", 2020, 100)
        predictor.add_data("cancer", 2021, 200)
        predictor.add_data("covid", 2020, 50)
        predictor.add_data("covid", 2021, 500)
        
        hot = predictor.get_hot_topics(top_n=2)
        
        assert len(hot) <= 2
