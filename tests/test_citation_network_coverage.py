"""Tests for citation_network module - Coverage improvement."""

import pytest
from unittest.mock import Mock, patch


class TestCitationNode:
    """Tests for CitationNode dataclass."""

    def test_citation_node_creation(self):
        """Test CitationNode creation."""
        from jarvis_core.analysis.citation_network import CitationNode

        node = CitationNode(
            paper_id="paper1",
            title="Test Paper",
            year=2024,
            citations_count=10,
        )

        assert node.paper_id == "paper1"
        assert node.title == "Test Paper"
        assert node.year == 2024
        assert node.citations_count == 10
        assert node.cited_by == []
        assert node.cites == []

    def test_to_dict(self):
        """Test CitationNode to_dict method."""
        from jarvis_core.analysis.citation_network import CitationNode

        node = CitationNode(
            paper_id="paper1",
            title="Test Paper",
            year=2024,
        )

        result = node.to_dict()

        assert isinstance(result, dict)
        assert result["paper_id"] == "paper1"
        assert result["title"] == "Test Paper"
        assert result["year"] == 2024


class TestCitationStats:
    """Tests for CitationStats dataclass."""

    def test_citation_stats_creation(self):
        """Test CitationStats creation."""
        from jarvis_core.analysis.citation_network import CitationStats

        stats = CitationStats(
            total_papers=100,
            total_citations=500,
            avg_citations=5.0,
            most_cited=[("paper1", 50), ("paper2", 40)],
            citation_distribution={"2023": 40, "2024": 60},
        )

        assert stats.total_papers == 100
        assert stats.total_citations == 500
        assert stats.avg_citations == 5.0

    def test_to_dict(self):
        """Test CitationStats to_dict method."""
        from jarvis_core.analysis.citation_network import CitationStats

        stats = CitationStats(
            total_papers=10,
            total_citations=50,
            avg_citations=5.0,
            most_cited=[],
            citation_distribution={},
        )

        result = stats.to_dict()

        assert isinstance(result, dict)
        assert result["total_papers"] == 10


class TestCitationNetwork:
    """Tests for CitationNetwork class."""

    def test_initialization(self):
        """Test CitationNetwork initialization."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()

        assert network.nodes == {}

    def test_add_paper(self):
        """Test adding a paper."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        node = network.add_paper("p1", "Paper 1", 2024, citations_count=5)

        assert node.paper_id == "p1"
        assert "p1" in network.nodes

    def test_add_paper_duplicate(self):
        """Test adding duplicate paper returns existing."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        node1 = network.add_paper("p1", "Paper 1", 2024)
        node2 = network.add_paper("p1", "Different Title", 2025)

        assert node1 is node2
        assert len(network.nodes) == 1

    def test_add_citation(self):
        """Test adding citation relationship."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        network.add_paper("p1", "Paper 1", 2024)
        network.add_paper("p2", "Paper 2", 2023)

        network.add_citation("p1", "p2")

        assert "p2" in network.nodes["p1"].cites
        assert "p1" in network.nodes["p2"].cited_by
        assert network.nodes["p2"].citations_count == 1

    def test_add_citation_missing_papers(self):
        """Test adding citation with missing papers."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        # Should not raise
        network.add_citation("missing1", "missing2")

    def test_get_stats_empty(self):
        """Test get_stats with empty network."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        stats = network.get_stats()

        assert stats.total_papers == 0
        assert stats.total_citations == 0
        assert stats.avg_citations == 0.0

    def test_get_stats_with_papers(self):
        """Test get_stats with papers."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        network.add_paper("p1", "Paper 1", 2024, citations_count=10)
        network.add_paper("p2", "Paper 2", 2023, citations_count=5)

        stats = network.get_stats()

        assert stats.total_papers == 2
        assert stats.total_citations == 15
        assert stats.avg_citations == 7.5

    def test_find_influential_papers(self):
        """Test finding influential papers."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        network.add_paper("p1", "Paper 1", 2024, citations_count=100)
        network.add_paper("p2", "Paper 2", 2023, citations_count=50)
        network.add_paper("p3", "Paper 3", 2022, citations_count=200)

        influential = network.find_influential_papers(top_n=2)

        assert len(influential) == 2
        assert influential[0].paper_id == "p3"  # Most cited
        assert influential[1].paper_id == "p1"

    def test_find_citing_chain(self):
        """Test finding citing chain."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        network.add_paper("p1", "Paper 1", 2024)
        network.add_paper("p2", "Paper 2", 2023)
        network.add_paper("p3", "Paper 3", 2022)

        network.add_citation("p1", "p2")
        network.add_citation("p2", "p3")

        chains = network.find_citing_chain("p1", max_depth=3)

        assert len(chains) > 0
        assert chains[0][0] == "p1"

    def test_find_citing_chain_missing_paper(self):
        """Test finding citing chain for missing paper."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        chains = network.find_citing_chain("missing")

        assert chains == []

    def test_to_networkx_success(self):
        """Test converting to NetworkX graph."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        network.add_paper("p1", "Paper 1", 2024)
        network.add_paper("p2", "Paper 2", 2023)
        network.add_citation("p1", "p2")

        # This may return None if networkx is not installed
        result = network.to_networkx()

        # Either None or a graph
        if result is not None:
            assert hasattr(result, "nodes")
            assert hasattr(result, "edges")

    def test_generate_report(self):
        """Test generating report."""
        from jarvis_core.analysis.citation_network import CitationNetwork

        network = CitationNetwork()
        network.add_paper("p1", "Important Paper", 2024, citations_count=100)
        network.add_paper("p2", "Another Paper", 2023, citations_count=50)

        report = network.generate_report()

        assert "Citation Network Report" in report
        assert "Important Paper" in report
        assert "100 citations" in report


class TestModuleImports:
    """Test module imports."""

    def test_imports(self):
        """Test all exports are importable."""
        from jarvis_core.analysis.citation_network import (
            CitationNode,
            CitationStats,
            CitationNetwork,
        )

        assert CitationNode is not None
        assert CitationStats is not None
        assert CitationNetwork is not None
