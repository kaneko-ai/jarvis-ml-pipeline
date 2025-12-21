"""Tests for RP29-37 Paper Vector Applications.

Tests all PaperVector-based analysis engines.
"""
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path
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
from jarvis_core.recommendation import recommend_papers
from jarvis_core.comparison import compare_papers
from jarvis_core.visualization.positioning import project_to_3d, get_position_description
from jarvis_core.hypothesis import generate_hypotheses
from jarvis_core.timeline import build_timeline, summarize_evolution
from jarvis_core.journal_targeting import suggest_journals
from jarvis_core.rehearsal import generate_rehearsal
from jarvis_core.education import translate_for_level
from jarvis_core.memory import search_memory, find_related, get_memory_stats


def _create_test_vectors():
    """Create test vectors for all tests."""
    return [
        PaperVector(
            paper_id="p1",
            source_locator="pdf:paper1.pdf",
            metadata=MetadataVector(year=2020),
            concept=ConceptVector(concepts={"CD73": 0.9, "Adenosine": 0.7}),
            method=MethodVector(methods={"scRNA-seq": 0.8}),
            biological_axis=BiologicalAxisVector(
                immune_activation=-0.5,
                tumor_context=0.8,
            ),
            temporal=TemporalVector(novelty=0.7),
            impact=ImpactVector(future_potential=0.6),
        ),
        PaperVector(
            paper_id="p2",
            source_locator="pdf:paper2.pdf",
            metadata=MetadataVector(year=2022),
            concept=ConceptVector(concepts={"PD-1": 0.8, "T cell": 0.6}),
            method=MethodVector(methods={"FACS": 0.9}),
            biological_axis=BiologicalAxisVector(
                immune_activation=0.6,
                tumor_context=0.3,
            ),
            temporal=TemporalVector(novelty=0.8),
            impact=ImpactVector(future_potential=0.7),
        ),
        PaperVector(
            paper_id="p3",
            source_locator="pdf:paper3.pdf",
            metadata=MetadataVector(year=2023),
            concept=ConceptVector(concepts={"CD73": 0.5, "PD-1": 0.4}),
            method=MethodVector(methods={"CRISPR": 0.7}),
            biological_axis=BiologicalAxisVector(
                immune_activation=0.2,
                metabolism_signal=-0.4,
                tumor_context=0.5,
            ),
            temporal=TemporalVector(novelty=0.9),
            impact=ImpactVector(future_potential=0.8),
        ),
    ]


class TestRecommendation:
    """Tests for RP29 Recommendation."""

    def test_recommend_by_concept(self):
        """Should rank by concept match."""
        vectors = _create_test_vectors()
        results = recommend_papers(vectors, ["CD73"])

        assert len(results) > 0
        assert results[0]["paper_id"] == "p1"  # Highest CD73

    def test_recommend_with_year_filter(self):
        """Should filter by year range."""
        vectors = _create_test_vectors()
        results = recommend_papers(
            vectors, ["CD73"], year_range=(2022, 2024)
        )

        assert all(r["year"] >= 2022 for r in results)

    def test_recommend_empty(self):
        """Should handle empty input."""
        assert recommend_papers([], ["CD73"]) == []


class TestComparison:
    """Tests for RP30 Comparison."""

    def test_compare_symmetric(self):
        """Comparison should be consistent."""
        vectors = _create_test_vectors()
        result = compare_papers(vectors[0], vectors[1])

        assert "paper_a" in result
        assert "paper_b" in result
        assert "summary" in result

    def test_compare_finds_differences(self):
        """Should identify differences."""
        vectors = _create_test_vectors()
        result = compare_papers(vectors[0], vectors[1])

        # They have different methods
        assert result["method_only_a"] or result["method_only_b"]


class TestPositioning:
    """Tests for RP31 3D Positioning."""

    def test_project_to_3d(self):
        """Should return 3D tuple."""
        pv = PaperVector(
            paper_id="test",
            source_locator="pdf:x",
            biological_axis=BiologicalAxisVector(0.5, -0.3, 0.8),
        )
        result = project_to_3d(pv)

        assert result == (0.5, -0.3, 0.8)

    def test_position_in_range(self):
        """Should be in [-1, 1]."""
        pv = PaperVector(paper_id="test", source_locator="pdf:x")
        x, y, z = project_to_3d(pv)

        assert -1 <= x <= 1
        assert -1 <= y <= 1
        assert -1 <= z <= 1

    def test_get_description(self):
        """Should generate meaningful description."""
        pv = PaperVector(
            paper_id="test",
            source_locator="pdf:x",
            biological_axis=BiologicalAxisVector(0.5, 0, 0.8),
        )
        desc = get_position_description(pv)

        assert "免疫活性化" in desc
        assert "TME" in desc


class TestHypothesis:
    """Tests for RP32 Hypothesis Generator."""

    def test_generate_hypotheses(self):
        """Should generate hypotheses."""
        vectors = _create_test_vectors()
        results = generate_hypotheses(vectors, ["CD73"])

        assert len(results) > 0
        assert "hypothesis" in results[0]
        assert "based_on" in results[0]

    def test_empty_input(self):
        """Should handle empty input."""
        assert generate_hypotheses([], ["CD73"]) == []


class TestTimeline:
    """Tests for RP33 Timeline."""

    def test_build_timeline(self):
        """Should build year-sorted timeline."""
        vectors = _create_test_vectors()
        timeline = build_timeline(vectors, "CD73")

        assert len(timeline) == 2  # p1 and p3 have CD73
        # Should be sorted by year
        if len(timeline) >= 2:
            assert timeline[0]["year"] <= timeline[1]["year"]

    def test_summarize_evolution(self):
        """Should summarize evolution."""
        vectors = _create_test_vectors()
        timeline = build_timeline(vectors, "CD73")
        summary = summarize_evolution(timeline)

        assert len(summary) > 0


class TestJournalTargeting:
    """Tests for RP34 Journal Targeting."""

    def test_suggest_journals(self):
        """Should suggest journals."""
        vectors = _create_test_vectors()
        results = suggest_journals(vectors)

        assert len(results) > 0
        assert "journal" in results[0]
        assert "fit_score" in results[0]

    def test_journal_ranking(self):
        """Should rank by fit."""
        vectors = _create_test_vectors()
        results = suggest_journals(vectors)

        scores = [r["fit_score"] for r in results]
        assert scores == sorted(scores, reverse=True)


class TestRehearsal:
    """Tests for RP35 Rehearsal."""

    def test_generate_rehearsal(self):
        """Should generate rehearsal questions."""
        vectors = _create_test_vectors()
        result = generate_rehearsal(vectors)

        assert "questions" in result
        assert "tough_questions" in result
        assert len(result["questions"]) > 0


class TestEducation:
    """Tests for RP36 Education."""

    def test_highschool_level(self):
        """Should generate simple explanation."""
        pv = _create_test_vectors()[0]
        result = translate_for_level(pv, "highschool")

        assert "高校生向け" in result

    def test_undergrad_level(self):
        """Should include concepts."""
        pv = _create_test_vectors()[0]
        result = translate_for_level(pv, "undergrad")

        assert "学部生向け" in result

    def test_grad_level(self):
        """Should be most detailed."""
        pv = _create_test_vectors()[0]
        result = translate_for_level(pv, "grad")

        assert "大学院生向け" in result
        assert "批判的評価" in result


class TestMemory:
    """Tests for RP37 Memory."""

    def test_search_memory_by_concept(self):
        """Should find by concept."""
        vectors = _create_test_vectors()
        results = search_memory(vectors, "CD73")

        assert len(results) > 0
        assert any(v.paper_id == "p1" for v in results)

    def test_find_related(self):
        """Should find related papers."""
        vectors = _create_test_vectors()
        results = find_related(vectors[0], vectors)

        assert len(results) > 0
        assert vectors[0] not in results  # Exclude self

    def test_get_memory_stats(self):
        """Should return stats."""
        vectors = _create_test_vectors()
        stats = get_memory_stats(vectors)

        assert stats["total_papers"] == 3
        assert stats["year_range"] == (2020, 2023)
