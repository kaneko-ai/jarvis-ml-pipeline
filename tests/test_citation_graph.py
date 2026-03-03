"""Tests for CitationGraph module."""
import json
import pytest
from jarvis_core.rag.citation_graph import CitationGraph


class TestCitationGraphBuild:
    def test_add_papers(self, sample_papers):
        cg = CitationGraph()
        added = cg.add_papers(sample_papers)
        assert added == 3
        assert cg.G.number_of_nodes() == 3

    def test_add_papers_dedup(self, sample_papers):
        cg = CitationGraph()
        cg.add_papers(sample_papers)
        added2 = cg.add_papers(sample_papers)
        assert added2 == 0
        assert cg.G.number_of_nodes() == 3

    def test_add_citation(self):
        cg = CitationGraph()
        cg.add_citation("paper_A", "paper_B")
        assert cg.G.number_of_nodes() == 2
        assert cg.G.number_of_edges() == 1
        assert cg.G.has_edge("paper_A", "paper_B")

    def test_add_citations_from_s2(self, sample_papers):
        sample_papers[0]["references"] = [
            {"paperId": "ref1", "doi": "", "title": "Referenced Paper 1"},
            {"paperId": "ref2", "doi": "", "title": "Referenced Paper 2"},
        ]
        sample_papers[1]["cited_by"] = [
            {"paperId": "citer1", "doi": "", "title": "Citing Paper 1"},
        ]
        cg = CitationGraph()
        cg.add_papers(sample_papers)
        edges = cg.add_citations_from_s2(sample_papers)
        assert edges == 3
        assert cg.G.number_of_edges() == 3


class TestCitationGraphAnalysis:
    def _build_graph(self):
        cg = CitationGraph()
        for i in range(5):
            cg.G.add_node(f"p{i}", title=f"Paper {i}", year=str(2020+i))
        cg.G.add_edge("p1", "p0")
        cg.G.add_edge("p2", "p0")
        cg.G.add_edge("p3", "p0")
        cg.G.add_edge("p4", "p1")
        return cg

    def test_stats(self):
        cg = self._build_graph()
        stats = cg.stats()
        assert stats["nodes"] == 5
        assert stats["edges"] == 4

    def test_find_hubs(self):
        cg = self._build_graph()
        hubs = cg.find_hubs(top_n=3)
        assert len(hubs) > 0
        assert hubs[0]["id"] == "p0"

    def test_find_clusters(self):
        cg = self._build_graph()
        clusters = cg.find_clusters()
        assert len(clusters) == 1
        assert len(clusters[0]) == 5

    def test_empty_graph(self):
        cg = CitationGraph()
        assert cg.stats() == {"nodes": 0, "edges": 0}
        assert cg.find_hubs() == []


class TestCitationGraphExport:
    def test_to_mermaid(self):
        cg = CitationGraph()
        cg.add_citation("A", "B")
        mmd = cg.to_mermaid()
        assert "graph LR" in mmd
        assert "-->" in mmd

    def test_to_obsidian_md(self):
        cg = CitationGraph()
        cg.add_citation("A", "B")
        md = cg.to_obsidian_md()
        assert "# Citation Network" in md
        assert "```mermaid" in md

    def test_save(self, tmp_path):
        cg = CitationGraph()
        cg.G.add_node("p1", title="Test Paper", year="2024")
        cg.add_citation("p1", "p2")
        paths = cg.save(str(tmp_path), prefix="test_net")
        assert "graphml" in paths
        assert "mermaid" in paths
        assert "obsidian_md" in paths
        assert "stats" in paths
        for p in paths.values():
            from pathlib import Path
            assert Path(p).exists()

    def test_from_json(self, sample_papers_json):
        cg = CitationGraph.from_json(sample_papers_json)
        assert cg.G.number_of_nodes() == 3
