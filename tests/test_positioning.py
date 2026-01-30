"""Tests for visualization.positioning module."""

from unittest.mock import MagicMock

from jarvis_core.visualization.positioning import (
    project_to_3d,
    project_all_to_3d,
    get_position_description,
)


def create_mock_paper(
    paper_id="p1",
    source_locator="loc1",
    year=2024,
    immune=0.0,
    metabolism=0.0,
    tumor=0.0,
    concepts=None,
):
    """Helper to create mock PaperVector."""
    paper = MagicMock()
    paper.paper_id = paper_id
    paper.source_locator = source_locator
    paper.metadata.year = year

    # BiologicalAxisVector mock
    paper.biological_axis.immune_activation = immune
    paper.biological_axis.metabolism_signal = metabolism
    paper.biological_axis.tumor_context = tumor
    paper.biological_axis.as_tuple.return_value = (immune, metabolism, tumor)

    # Concept mock
    paper.concept.concepts = concepts or {}
    if concepts:
        paper.concept.top_concepts.return_value = [(list(concepts.keys())[0], 1.0)]
    else:
        paper.concept.top_concepts.return_value = []

    return paper


class TestProjectTo3D:
    def test_basic_projection(self):
        paper = create_mock_paper(immune=0.5, metabolism=-0.3, tumor=0.8)
        x, y, z = project_to_3d(paper)

        assert x == 0.5
        assert y == -0.3
        assert z == 0.8


class TestProjectAllTo3D:
    def test_project_multiple_papers(self):
        papers = [
            create_mock_paper("p1", "loc1", 2023, 0.1, 0.2, 0.3, {"concept1": 1.0}),
            create_mock_paper("p2", "loc2", 2024, -0.1, -0.2, -0.3, {"concept2": 0.8}),
        ]

        results = project_all_to_3d(papers)

        assert len(results) == 2
        assert results[0]["paper_id"] == "p1"
        assert results[0]["x"] == 0.1
        assert results[0]["year"] == 2023
        assert results[1]["paper_id"] == "p2"
        assert results[1]["z"] == -0.3

    def test_project_empty_list(self):
        results = project_all_to_3d([])
        assert results == []


class TestGetPositionDescription:
    def test_immune_activation(self):
        paper = create_mock_paper(immune=0.5, metabolism=0.0, tumor=0.0)
        desc = get_position_description(paper)
        assert "免疫活性化領域" in desc

    def test_immune_suppression(self):
        paper = create_mock_paper(immune=-0.5, metabolism=0.0, tumor=0.0)
        desc = get_position_description(paper)
        assert "免疫抑制領域" in desc

    def test_metabolism_focus(self):
        paper = create_mock_paper(immune=0.0, metabolism=-0.5, tumor=0.0)
        desc = get_position_description(paper)
        assert "代謝重視" in desc

    def test_signal_focus(self):
        paper = create_mock_paper(immune=0.0, metabolism=0.5, tumor=0.0)
        desc = get_position_description(paper)
        assert "シグナル重視" in desc

    def test_tme_local(self):
        paper = create_mock_paper(immune=0.0, metabolism=0.0, tumor=0.5)
        desc = get_position_description(paper)
        assert "TME局所研究" in desc

    def test_systemic_immune(self):
        paper = create_mock_paper(immune=0.0, metabolism=0.0, tumor=-0.5)
        desc = get_position_description(paper)
        assert "全身免疫研究" in desc

    def test_neutral_returns_standard(self):
        paper = create_mock_paper(immune=0.0, metabolism=0.0, tumor=0.0)
        desc = get_position_description(paper)
        assert desc == "免疫中立"

    def test_combined_description(self):
        paper = create_mock_paper(immune=0.5, metabolism=0.5, tumor=0.5)
        desc = get_position_description(paper)
        assert "免疫活性化領域" in desc
        assert "シグナル重視" in desc
        assert "TME局所研究" in desc