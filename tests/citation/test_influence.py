"""Tests for Citation Influence Calculator."""

from jarvis_core.citation.influence import InfluenceCalculator
from jarvis_core.citation.stance_classifier import CitationStance


class MockCitation:
    def __init__(self, stance):
        self.stance = stance


def test_influence_score_calculation():
    calculator = InfluenceCalculator()

    citations = [
        MockCitation(CitationStance.SUPPORT),
        MockCitation(CitationStance.SUPPORT),
        MockCitation(CitationStance.CONTRAST),
        MockCitation(CitationStance.MENTION),
    ]

    score = calculator.calculate("paper123", citations)

    assert score.paper_id == "paper123"
    assert score.total_citations == 4
    assert score.support_count == 2
    assert score.contrast_count == 1
    assert score.mention_count == 1
    assert score.influence_score > 0


def test_rank_papers_by_influence():
    calculator = InfluenceCalculator()

    citations_map = {
        "paper1": [MockCitation(CitationStance.SUPPORT)] * 10,
        "paper2": [MockCitation(CitationStance.SUPPORT)] * 5,
        "paper3": [],  # No citations
    }

    ranked = calculator.rank_papers(["paper1", "paper2", "paper3"], citations_map, by="influence")

    assert len(ranked) == 3
    # paper1 should have highest influence (10 supports)
    assert ranked[0].paper_id == "paper1"


def test_empty_citations():
    calculator = InfluenceCalculator()
    score = calculator.calculate("empty_paper", [])

    assert score.total_citations == 0
    assert score.influence_score == 0.0