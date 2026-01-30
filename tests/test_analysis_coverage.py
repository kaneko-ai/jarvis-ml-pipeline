"""Tests for analysis module - Coverage improvement (FIXED)."""

from unittest.mock import Mock


class TestComparisonRow:
    """Tests for ComparisonRow dataclass."""

    def test_comparison_row_creation(self):
        """Test ComparisonRow creation."""
        from jarvis_core.analysis.comparison import ComparisonRow

        row = ComparisonRow(
            paper_id="p1",
            title="Test Paper",
            year=2024,
            method="RCT",
            sample_size="100",
            key_result="Positive effect",
            limitations="Small sample",
        )

        assert row.paper_id == "p1"
        assert row.title == "Test Paper"
        assert row.year == 2024

    def test_to_dict(self):
        """Test ComparisonRow to_dict."""
        from jarvis_core.analysis.comparison import ComparisonRow

        row = ComparisonRow(
            paper_id="p1",
            title="Test",
            year=2024,
            method="RCT",
            sample_size="50",
            key_result="Result",
            limitations="None",
        )

        result = row.to_dict()
        assert result["paper_id"] == "p1"
        assert result["method"] == "RCT"


class TestComparisonTable:
    """Tests for ComparisonTable dataclass."""

    def test_comparison_table_creation(self):
        """Test ComparisonTable creation."""
        from jarvis_core.analysis.comparison import ComparisonTable

        table = ComparisonTable(
            title="Test Comparison",
            columns=["Paper", "Year", "Method"],
        )

        assert table.title == "Test Comparison"
        assert len(table.columns) == 3
        assert table.rows == []

    def test_to_dict(self):
        """Test ComparisonTable to_dict."""
        from jarvis_core.analysis.comparison import ComparisonTable

        table = ComparisonTable(
            title="Test",
            columns=["A", "B"],
        )

        result = table.to_dict()
        assert result["title"] == "Test"
        assert result["columns"] == ["A", "B"]

    def test_to_markdown(self):
        """Test ComparisonTable to_markdown."""
        from jarvis_core.analysis.comparison import ComparisonTable, ComparisonRow

        row = ComparisonRow(
            paper_id="p1",
            title="Long Paper Title That Exceeds Limit",
            year=2024,
            method="Randomized Controlled Trial",
            sample_size="100",
            key_result="This is a very long key result that should be truncated",
            limitations="Some limitations here",
        )

        table = ComparisonTable(
            title="Test Comparison",
            columns=["Paper", "Year"],
            rows=[row],
        )

        markdown = table.to_markdown()
        assert "Test Comparison" in markdown
        assert "2024" in markdown

    def test_to_html(self):
        """Test ComparisonTable to_html."""
        from jarvis_core.analysis.comparison import ComparisonTable, ComparisonRow

        row = ComparisonRow(
            paper_id="p1",
            title="Test Paper",
            year=2024,
            method="RCT",
            sample_size="50",
            key_result="Result",
            limitations="None",
        )

        table = ComparisonTable(
            title="Test",
            columns=["Paper"],
            rows=[row],
        )

        html = table.to_html()
        assert "<table" in html
        assert "Test Paper" in html


class TestComparisonAnalyzer:
    """Tests for ComparisonAnalyzer class."""

    def test_analyzer_creation(self):
        """Test ComparisonAnalyzer creation."""
        from jarvis_core.analysis.comparison import ComparisonAnalyzer

        analyzer = ComparisonAnalyzer()
        assert analyzer.llm_client is None

    def test_analyzer_with_llm(self):
        """Test ComparisonAnalyzer with LLM client."""
        from jarvis_core.analysis.comparison import ComparisonAnalyzer

        mock_llm = Mock()
        analyzer = ComparisonAnalyzer(llm_client=mock_llm)
        assert analyzer.llm_client is mock_llm

    def test_analyze(self):
        """Test analyze method."""
        from jarvis_core.analysis.comparison import ComparisonAnalyzer

        analyzer = ComparisonAnalyzer()
        papers = [
            {
                "paper_id": "p1",
                "title": "Test Paper 1",
                "year": 2024,
                "abstract": "This is a randomized trial studying...",
            },
            {
                "paper_id": "p2",
                "title": "Test Paper 2",
                "year": 2023,
                "abstract": "This cohort study examines...",
            },
        ]

        table = analyzer.analyze(papers)
        assert table is not None
        assert len(table.rows) == 2

    def test_analyze_with_claims(self):
        """Test analyze with claims."""
        from jarvis_core.analysis.comparison import ComparisonAnalyzer

        analyzer = ComparisonAnalyzer()
        papers = [
            {"paper_id": "p1", "title": "Paper 1", "year": 2024, "abstract": "Meta-analysis of..."},
        ]
        claims = [
            {"paper_id": "p1", "claim_type": "finding", "claim_text": "Drug X is effective"},
        ]

        table = analyzer.analyze(papers, claims)
        assert len(table.rows) == 1

    def test_generate_summary(self):
        """Test generate_summary method."""
        from jarvis_core.analysis.comparison import (
            ComparisonAnalyzer,
            ComparisonTable,
            ComparisonRow,
        )

        analyzer = ComparisonAnalyzer()
        row = ComparisonRow(
            paper_id="p1",
            title="Test",
            year=2024,
            method="RCT",
            sample_size="100",
            key_result="Result",
            limitations="None",
        )
        table = ComparisonTable(title="Test", columns=["A"], rows=[row])

        summary = analyzer.generate_summary(table)
        assert "Total papers" in summary
        assert "1" in summary


class TestCitationNetwork:
    """Tests for CitationNetwork (from citation_network module)."""

    def test_citation_network_creation(self):
        """Test CitationNetwork creation."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        assert network.nodes == {}


class TestContradictionModule:
    """Tests for contradiction detection module."""

    def test_contradiction_detector_creation(self):
        """Test ContradictionDetector creation."""
        from jarvis_core.analysis.contradiction import ContradictionDetector

        detector = ContradictionDetector()
        assert detector is not None


class TestEvidenceMapperModule:
    """Tests for evidence mapper module."""

    def test_evidence_mapper_creation(self):
        """Test EvidenceMapper creation."""
        from jarvis_core.analysis.evidence_mapper import EvidenceMapper

        mapper = EvidenceMapper()
        assert mapper is not None


class TestKnowledgeGraphModule:
    """Tests for knowledge graph module."""

    def test_knowledge_graph_creation(self):
        """Test KnowledgeGraph creation."""
        from jarvis_core.analysis.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        assert kg is not None


class TestReviewGeneratorModule:
    """Tests for review generator module."""

    def test_review_generator_creation(self):
        """Test ReviewGenerator creation."""
        from jarvis_core.analysis.review_generator import ReviewGenerator

        gen = ReviewGenerator()
        assert gen is not None


class TestModuleImports:
    """Test module imports."""

    def test_analysis_imports(self):
        """Test analysis module imports."""
        from jarvis_core.analysis import CitationNetwork
        from jarvis_core.analysis.comparison import ComparisonAnalyzer

        assert CitationNetwork is not None
        assert ComparisonAnalyzer is not None