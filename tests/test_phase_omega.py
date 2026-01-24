import pytest
"""Tests for Phase ﾎｩ (Research OS v2.0 Core).

Tests ﾎｩ-1 to ﾎｩ-10 modules.
"""

from jarvis_core.autonomous_loop import get_intervention_summary, run_autonomous_research_loop
from jarvis_core.experimental.career_planner import plan_career_strategy
from jarvis_core.cross_field import find_cross_field_opportunities
from jarvis_core.experimental.failure_simulator import simulate_failure_tree
from jarvis_core.experimental.grant_optimizer import optimize_grant_proposal, suggest_grant_improvements
from jarvis_core.knowledge_graph import build_knowledge_graph
from jarvis_core.experimental.lab_optimizer import optimize_lab_resources
from jarvis_core.living_review import generate_living_review, update_living_review
from jarvis_core.paper_vector import (
    BiologicalAxisVector,
    ConceptVector,
    ImpactVector,
    MetadataVector,
    MethodVector,
    PaperVector,
    TemporalVector,
)
from jarvis_core.experimental.pi_support import evaluate_research_themes, generate_pi_summary
from jarvis_core.reviewer_persona import generate_all_reviewer_feedback, generate_reviewer_feedback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


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

@pytest.mark.slow
class TestAutonomousLoop:
    """ﾎｩ-1 tests."""

    def test_loop_completes(self):
        vectors = _create_test_vectors()
        result = run_autonomous_research_loop(vectors, ["CD73"], max_iterations=2)
        assert result["status"] == "completed"
        assert len(result["iterations"]) <= 2

    def test_loop_logs_iterations(self):
        vectors = _create_test_vectors()
        result = run_autonomous_research_loop(vectors, ["CD73"], max_iterations=1)
        assert len(result["iterations"]) == 1
        assert "gap_analysis" in result["iterations"][0]

    def test_intervention_points(self):
        vectors = _create_test_vectors()
        result = run_autonomous_research_loop(vectors, ["CD73"], max_iterations=1)
        summary = get_intervention_summary(result)
        assert isinstance(summary, str)

    def test_empty_input(self):
        result = run_autonomous_research_loop([], ["CD73"])
        assert result["status"] == "no_input"

class TestCrossField:
    """ﾎｩ-5 tests."""

    def test_finds_opportunities(self):
        vectors = _create_test_vectors()
        opps = find_cross_field_opportunities(vectors)
        assert isinstance(opps, list)

    def test_empty_safe(self):
        opps = find_cross_field_opportunities([])
        assert opps == []

class TestFailureSimulator:
    """ﾎｩ-7 tests."""

    def test_generates_tree(self):
        vectors = _create_test_vectors()
        tree = simulate_failure_tree("CD73 immune hypothesis", vectors)
        assert "branches" in tree
        assert tree["estimated"] is True

    def test_failure_probability(self):
        vectors = _create_test_vectors()
        tree = simulate_failure_tree("test", vectors)
        assert 0 <= tree["overall_failure_probability"] <= 1

    def test_mitigation_strategies(self):
        vectors = _create_test_vectors()
        tree = simulate_failure_tree("test", vectors)
        assert len(tree["mitigation_strategies"]) > 0

class TestLivingReview:
    """ﾎｩ-8 tests."""

    def test_generates_review(self):
        vectors = _create_test_vectors()
        review = generate_living_review(vectors, "CD73")
        assert "sections" in review
        assert review["version"] == 1

    def test_update_review(self):
        vectors = _create_test_vectors()
        review = generate_living_review(vectors, "CD73")
        updated = update_living_review(review, vectors)
        assert updated["version"] == 2

class TestKnowledgeGraph:
    """ﾎｩ-9 tests."""

    def test_builds_graph(self):
        vectors = _create_test_vectors()
        graph = build_knowledge_graph(vectors)
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0

    def test_hybrid_similarity(self):
        vectors = _create_test_vectors()
        graph = build_knowledge_graph(vectors)
        sim = graph.get_hybrid_similarity("p1", "p2")
        assert 0 <= sim <= 1

class TestGrantOptimizer:
    """ﾎｩ-2 tests."""

    def test_optimizes_grant(self):
        vectors = _create_test_vectors()
        result = optimize_grant_proposal(vectors, ["CD73", "immune"])
        assert "score" in result
        assert result["estimated"] is True

    def test_suggests_improvements(self):
        result = {"alignment": 0.3, "novelty": 0.3, "risks": ["莠亥ｙ繝・・繧ｿ荳崎ｶｳ"]}
        suggestions = suggest_grant_improvements(result)
        assert len(suggestions) > 0

class TestReviewerPersona:
    """ﾎｩ-3 tests."""

    def test_generates_feedback(self):
        vectors = _create_test_vectors()
        feedback = generate_reviewer_feedback(vectors, "strict")
        assert feedback["persona"] == "strict"
        assert len(feedback["comments"]) > 0

    def test_all_personas(self):
        vectors = _create_test_vectors()
        all_fb = generate_all_reviewer_feedback(vectors)
        assert len(all_fb) == 3

class TestLabOptimizer:
    """ﾎｩ-4 tests."""

    def test_optimizes_resources(self):
        vectors = _create_test_vectors()
        result = optimize_lab_resources("CD73 experiment", vectors)
        assert "path" in result

class TestCareerPlanner:
    """ﾎｩ-6 tests."""

    def test_plans_career(self):
        vectors = _create_test_vectors()
        plan = plan_career_strategy(vectors, "phd")
        assert plan["stage"] == "phd"
        assert len(plan["recommendations"]) > 0

class TestPISupport:
    """ﾎｩ-10 tests."""

    def test_evaluates_themes(self):
        vectors = _create_test_vectors()
        evals = evaluate_research_themes({"theme1": vectors})
        assert len(evals) == 1
        assert evals[0]["estimated"] is True

    def test_generates_summary(self):
        vectors = _create_test_vectors()
        evals = evaluate_research_themes({"theme1": vectors})
        summary = generate_pi_summary(evals)
        assert "繧ｵ繝槭Μ繝ｼ" in summary
