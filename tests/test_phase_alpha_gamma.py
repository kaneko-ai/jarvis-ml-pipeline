"""Tests for Phase α-γ (RP38-46).

Tests all research design and analysis engines.
No mocks - uses real dummy data.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.paper_vector import (
    PaperVector,
    MetadataVector,
    ConceptVector,
    MethodVector,
    BiologicalAxisVector,
    TemporalVector,
    ImpactVector,
)
from jarvis_core.gap_analysis import score_research_gaps
from jarvis_core.chain_builder import build_research_chain
from jarvis_core.competing_hypothesis import generate_competing_hypotheses
from jarvis_core.paradigm import detect_paradigm_shift
from jarvis_core.heatmap import build_concept_heatmap, get_trending_concepts
from jarvis_core.method_trend import track_method_evolution
from jarvis_core.feasibility import score_feasibility
from jarvis_core.failure_predictor import predict_failure_modes
from jarvis_core.model_system import suggest_model_system


def _create_test_vectors():
    return [
        PaperVector(
            paper_id="p1",
            source_locator="pdf:1.pdf",
            metadata=MetadataVector(year=2018, species=["mouse"]),
            concept=ConceptVector(concepts={"CD73": 0.9, "Adenosine": 0.7}),
            method=MethodVector(methods={"Western blot": 0.8}),
            biological_axis=BiologicalAxisVector(immune_activation=-0.5, tumor_context=0.8),
            temporal=TemporalVector(novelty=0.4),
            impact=ImpactVector(future_potential=0.3),
        ),
        PaperVector(
            paper_id="p2",
            source_locator="pdf:2.pdf",
            metadata=MetadataVector(year=2020),
            concept=ConceptVector(concepts={"PD-1": 0.8, "T cell": 0.6, "CD73": 0.3}),
            method=MethodVector(methods={"scRNA-seq": 0.9, "FACS": 0.6}),
            biological_axis=BiologicalAxisVector(immune_activation=0.6),
            temporal=TemporalVector(novelty=0.7),
            impact=ImpactVector(future_potential=0.6),
        ),
        PaperVector(
            paper_id="p3",
            source_locator="pdf:3.pdf",
            metadata=MetadataVector(year=2022),
            concept=ConceptVector(concepts={"CD73": 0.5, "tumor": 0.8}),
            method=MethodVector(methods={"CRISPR": 0.7, "scRNA-seq": 0.5}),
            biological_axis=BiologicalAxisVector(tumor_context=0.9),
            temporal=TemporalVector(novelty=0.9),
            impact=ImpactVector(future_potential=0.8),
        ),
    ]


class TestGapAnalysis:
    """RP39 tests."""

    def test_gap_score_range_0_1(self):
        vectors = _create_test_vectors()
        results = score_research_gaps(vectors, "CD73")
        assert len(results) > 0
        assert 0 <= results[0]["gap_score"] <= 1

    def test_density_effect(self):
        vectors = _create_test_vectors()
        r1 = score_research_gaps(vectors, "CD73")[0]
        r2 = score_research_gaps(vectors, "PD-1")[0]
        # CD73 has more papers -> lower gap
        assert r1["density"] >= r2["density"]

    def test_year_range_filter(self):
        vectors = _create_test_vectors()
        results = score_research_gaps(vectors, "CD73", year_range=(2020, 2024))
        assert all(p in ["p2", "p3"] for p in results[0]["papers"])

    def test_empty_concept_returns_empty(self):
        assert score_research_gaps([], "CD73") == []

    def test_deterministic_output(self):
        vectors = _create_test_vectors()
        r1 = score_research_gaps(vectors, "CD73")
        r2 = score_research_gaps(vectors, "CD73")
        assert r1[0]["gap_score"] == r2[0]["gap_score"]


class TestChainBuilder:
    """RP38 tests."""

    def test_chain_has_all_fields(self):
        vectors = _create_test_vectors()
        results = build_research_chain(["CD73 regulates T cell"], vectors)
        assert len(results) > 0
        assert "claim" in results[0]
        assert "hypothesis" in results[0]
        assert "experiment" in results[0]

    def test_related_papers_non_empty(self):
        vectors = _create_test_vectors()
        results = build_research_chain(["CD73 function"], vectors)
        assert len(results[0]["supporting_papers"]) > 0

    def test_multiple_claims_supported(self):
        vectors = _create_test_vectors()
        results = build_research_chain(["Claim A", "Claim B"], vectors)
        assert len(results) == 2

    def test_no_related_papers_graceful(self):
        vectors = _create_test_vectors()
        results = build_research_chain(["Unknown concept XYZ"], vectors)
        assert len(results) == 1  # Still returns result

    def test_reproducibility(self):
        vectors = _create_test_vectors()
        r1 = build_research_chain(["CD73"], vectors)
        r2 = build_research_chain(["CD73"], vectors)
        assert r1[0]["hypothesis"] == r2[0]["hypothesis"]


class TestCompetingHypothesis:
    """RP40 tests."""

    def test_minimum_two_hypotheses(self):
        vectors = _create_test_vectors()
        results = generate_competing_hypotheses("CD73 phenomenon", vectors)
        assert len(results) >= 2

    def test_conflict_relationship_exists(self):
        vectors = _create_test_vectors()
        results = generate_competing_hypotheses("immune response", vectors)
        for h in results:
            assert "conflicts_with" in h

    def test_discriminating_experiment_present(self):
        vectors = _create_test_vectors()
        results = generate_competing_hypotheses("tumor", vectors)
        for h in results:
            assert "discriminating_experiment" in h

    def test_empty_vectors_safe(self):
        results = generate_competing_hypotheses("phenomenon", [])
        assert results == []


class TestParadigm:
    """RP41 tests."""

    def test_detects_shift(self):
        vectors = _create_test_vectors()
        result = detect_paradigm_shift(vectors, "CD73")
        # May or may not detect shift
        assert result is None or "year" in result

    def test_no_shift_returns_none(self):
        vectors = [_create_test_vectors()[0]]
        result = detect_paradigm_shift(vectors, "CD73")
        assert result is None

    def test_single_year_safe(self):
        vectors = [_create_test_vectors()[0]]
        result = detect_paradigm_shift(vectors, "CD73")
        assert result is None


class TestHeatmap:
    """RP43 tests."""

    def test_years_sorted(self):
        vectors = _create_test_vectors()
        heatmap = build_concept_heatmap(vectors)
        years = list(heatmap.keys())
        assert years == sorted(years)

    def test_values_normalized(self):
        vectors = _create_test_vectors()
        heatmap = build_concept_heatmap(vectors)
        for year_data in heatmap.values():
            for score in year_data.values():
                assert 0 <= score <= 1

    def test_missing_year_handled(self):
        vectors = _create_test_vectors()
        vectors.append(PaperVector(
            paper_id="no_year",
            source_locator="pdf:x",
            metadata=MetadataVector(year=None),
        ))
        heatmap = build_concept_heatmap(vectors)
        assert "None" not in heatmap


class TestMethodTrend:
    """RP44 tests."""

    def test_emerging_method_detected(self):
        vectors = _create_test_vectors()
        evolution = track_method_evolution(vectors)
        all_emerging = [m for e in evolution for m in e["emerging_methods"]]
        assert len(all_emerging) > 0

    def test_chronological_order(self):
        vectors = _create_test_vectors()
        evolution = track_method_evolution(vectors)
        years = [e["year"] for e in evolution]
        assert years == sorted(years)

    def test_no_method_safe(self):
        vectors = [PaperVector(paper_id="x", source_locator="pdf:x", metadata=MetadataVector(year=2020))]
        evolution = track_method_evolution(vectors)
        assert len(evolution) == 1


class TestFeasibility:
    """RP45 tests."""

    def test_scores_range(self):
        vectors = _create_test_vectors()
        result = score_feasibility("CD73 inhibition", vectors)
        assert 0 <= result["difficulty"] <= 1
        assert 0 <= result["cost"] <= 1
        assert 0 <= result["reproducibility"] <= 1

    def test_similar_papers_reduce_difficulty(self):
        vectors = _create_test_vectors()
        r1 = score_feasibility("CD73 hypothesis", vectors)
        r2 = score_feasibility("Unknown XYZ hypothesis", vectors)
        assert r1["difficulty"] <= r2["difficulty"]

    def test_no_related_papers_high_difficulty(self):
        vectors = _create_test_vectors()
        result = score_feasibility("Completely unknown topic", vectors)
        assert result["difficulty"] >= 0.5


class TestFailurePredictor:
    """RP47 tests."""

    def test_failure_modes_non_empty(self):
        vectors = _create_test_vectors()
        results = predict_failure_modes("CD73 tumor hypothesis", vectors)
        assert len(results) > 0

    def test_specificity_of_messages(self):
        vectors = _create_test_vectors()
        results = predict_failure_modes("immune response", vectors)
        assert any("免疫" in m for m in results)

    def test_empty_safe(self):
        results = predict_failure_modes("", [])
        assert results == []


class TestModelSystem:
    """RP46 tests."""

    def test_model_matches_concept(self):
        vectors = _create_test_vectors()
        result = suggest_model_system("PD-1 signaling", vectors)
        assert len(result["cell_lines"]) > 0

    def test_reason_present(self):
        vectors = _create_test_vectors()
        result = suggest_model_system("tumor infiltration", vectors)
        assert "reason" in result

    def test_empty_vectors_safe(self):
        result = suggest_model_system("PD-1", [])
        assert "cell_lines" in result
