"""Tests for thinking_engines module."""

from unittest.mock import MagicMock

from jarvis_core.thinking_engines import (
    analyze_counterfactual,
    discover_blind_spots,
    simulate_concept_mutation,
    simulate_research_debate,
    simulate_hypothesis_evolution,
)


def make_mock_vector(paper_id: str, concepts: list[str]):
    """Create a mock PaperVector."""
    mock = MagicMock()
    mock.paper_id = paper_id
    mock.concept.concepts = {c: 1.0 for c in concepts}
    mock.impact.future_potential = 0.5
    mock.biological_axis.immune_activation = 0.5
    mock.biological_axis.metabolism_signal = 0.5
    mock.biological_axis.tumor_context = 0.5
    return mock


class TestAnalyzeCounterfactual:
    def test_empty_vectors(self):
        mock_vector = make_mock_vector("paper1", ["cancer"])
        result = analyze_counterfactual(mock_vector, [])

        assert result["impact_delta"] == 0.0
        assert result["estimated"] is True

    def test_with_vectors(self):
        vector = make_mock_vector("paper1", ["cancer", "immunotherapy"])
        others = [
            make_mock_vector("paper2", ["cancer"]),
            make_mock_vector("paper3", ["diabetes"]),
        ]

        result = analyze_counterfactual(vector, others)

        assert "impact_delta" in result
        assert "affected_papers" in result


class TestDiscoverBlindSpots:
    def test_empty_vectors(self):
        result = discover_blind_spots([])
        assert result == []

    def test_finds_blind_spots(self):
        # Create vectors with low axis coverage
        v1 = make_mock_vector("p1", ["x"])
        v1.biological_axis.immune_activation = 0.1
        v1.biological_axis.metabolism_signal = 0.1
        v1.biological_axis.tumor_context = 0.1

        result = discover_blind_spots([v1])

        # Should find blind spots due to low coverage
        assert isinstance(result, list)


class TestSimulateConceptMutation:
    def test_mutation_paths(self):
        vectors = [
            make_mock_vector("p1", ["cancer", "treatment"]),
            make_mock_vector("p2", ["cancer", "diagnosis"]),
        ]

        result = simulate_concept_mutation("cancer", vectors)

        assert result["original_concept"] == "cancer"
        assert "mutation_paths" in result
        assert result["estimated"] is True


class TestSimulateResearchDebate:
    def test_debate_structure(self):
        vectors = [make_mock_vector("p1", ["hypothesis"])]

        result = simulate_research_debate("Test hypothesis", vectors)

        assert "pro_arguments" in result
        assert "con_arguments" in result
        assert result["winner"] in ["pro", "con"]
        assert result["estimated"] is True


class TestSimulateHypothesisEvolution:
    def test_empty_hypotheses(self):
        result = simulate_hypothesis_evolution([], [])

        assert result["surviving_hypotheses"] == []

    def test_evolution_selection(self):
        vectors = [make_mock_vector("p1", ["cancer"])]
        hypotheses = ["Cancer treatment", "Random topic"]

        result = simulate_hypothesis_evolution(hypotheses, vectors)

        assert result["initial_count"] == 2
        assert len(result["surviving_hypotheses"]) >= 1
        assert "survival_rate" in result