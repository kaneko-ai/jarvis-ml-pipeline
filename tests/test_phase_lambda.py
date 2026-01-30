"""Tests for Phase ΁E(Extended Analysis Modules).

Tests ΁E1 to ΁E30 functions.
"""

from jarvis_core.experimental.lambda_modules import (
    alert_decision_delay,
    # ΁E1〜΁E5
    analyze_hypothesis_risks,
    # ΁E6〜΁E10
    build_experiment_dependency_graph,
    check_figure_claim_consistency,
    # ΁E21〜΁E25
    classify_hypothesis_type,
    classify_thinking_style,
    cluster_researchers,
    detect_claim_ambiguity,
    detect_cross_field_citations,
    detect_emerging_journals,
    detect_experiment_bottleneck,
    detect_reproduction_failure_signs,
    # ΁E11〜΁E15
    detect_reviewer_fatigue_points,
    # ΁E16〜΁E20
    detect_rising_concepts,
    detect_theme_overlap,
    detect_undervaluation,
    diagnose_research_speed,
    evaluate_citation_balance,
    generate_monthly_inventory,
    generate_monthly_strategy_brief,
    optimize_experiment_order,
    optimize_for_notebooklm,
    predict_technique_lifespan,
    # ΁E26〜΁E30
    restructure_for_obsidian,
    score_concept_competition,
    suggest_log_improvements,
    warn_control_shortage,
    warn_misleading_expressions,
    warn_strong_assumptions,
    warn_supplement_bloat,
)
from jarvis_core.paper_vector import (
    ConceptVector,
    ImpactVector,
    MetadataVector,
    MethodVector,
    PaperVector,
    TemporalVector,
)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


def _create_test_vectors():
    return [
        PaperVector(
            paper_id="p1",
            source_locator="pdf:1.pdf",
            metadata=MetadataVector(year=2022),
            concept=ConceptVector(concepts={"CD73": 0.9}),
            method=MethodVector(methods={"Western blot": 0.8}),
            temporal=TemporalVector(novelty=0.4),
            impact=ImpactVector(future_potential=0.3),
        ),
        PaperVector(
            paper_id="p2",
            source_locator="pdf:2.pdf",
            metadata=MetadataVector(year=2023),
            concept=ConceptVector(concepts={"PD-1": 0.8}),
            method=MethodVector(methods={"scRNA-seq": 0.9}),
            temporal=TemporalVector(novelty=0.8),
            impact=ImpactVector(future_potential=0.7),
        ),
    ]


class TestLambda1_5:
    def test_hypothesis_risks(self):
        vectors = _create_test_vectors()
        result = analyze_hypothesis_risks("CD73 hypothesis", vectors)
        assert "risks" in result

    def test_concept_competition(self):
        vectors = _create_test_vectors()
        result = score_concept_competition("CD73", "PD-1", vectors)
        assert "competition_score" in result

    def test_theme_overlap(self):
        result = detect_theme_overlap(["theme1", "theme2"], [])
        assert isinstance(result, list)

    def test_claim_ambiguity(self):
        result = detect_claim_ambiguity("This may be true")
        assert result["ambiguity_score"] > 0

    def test_strong_assumptions(self):
        result = warn_strong_assumptions("This definitely proves")
        assert "definitely" in result


class TestLambda6_10:
    def test_experiment_graph(self):
        result = build_experiment_dependency_graph(["E1", "E2"])
        assert len(result["nodes"]) == 2

    def test_bottleneck(self):
        result = detect_experiment_bottleneck(["E1", "E2"], [10, 50])
        assert result["bottleneck"] == "E2"

    def test_control_shortage(self):
        result = warn_control_shortage(["knockout"])
        assert len(result) > 0

    def test_experiment_order(self):
        result = optimize_experiment_order(["E1", "E2"], [50, 10])
        assert result[0] == "E2"

    def test_reproduction_signs(self):
        vectors = _create_test_vectors()
        result = detect_reproduction_failure_signs(vectors)
        assert isinstance(result, list)


class TestLambda11_15:
    def test_reviewer_fatigue(self):
        result = detect_reviewer_fatigue_points("Short text")
        assert isinstance(result, list)

    def test_misleading(self):
        result = warn_misleading_expressions("This clearly shows")
        assert "clearly shows" in result

    def test_figure_claim(self):
        result = check_figure_claim_consistency(["F1", "F2"], ["C1", "C2", "C3"])
        assert "consistency_score" in result

    def test_supplement_bloat(self):
        result = warn_supplement_bloat(60)
        assert "肥大" in result

    def test_citation_balance(self):
        vectors = _create_test_vectors()
        result = evaluate_citation_balance(vectors)
        assert "balance" in result


class TestLambda16_20:
    def test_rising_concepts(self):
        vectors = _create_test_vectors()
        result = detect_rising_concepts(vectors)
        assert isinstance(result, list)

    def test_technique_lifespan(self):
        vectors = _create_test_vectors()
        result = predict_technique_lifespan("scRNA-seq", vectors)
        assert result["estimated"] is True

    def test_emerging_journals(self):
        vectors = _create_test_vectors()
        result = detect_emerging_journals(vectors)
        assert isinstance(result, list)

    def test_cluster_researchers(self):
        vectors = _create_test_vectors()
        result = cluster_researchers(vectors)
        assert "clusters" in result

    def test_cross_field(self):
        vectors = _create_test_vectors()
        result = detect_cross_field_citations(vectors)
        assert result >= 0


class TestLambda21_25:
    def test_hypothesis_type(self):
        result = classify_hypothesis_type("mechanism of action")
        assert result == "mechanistic"

    def test_thinking_style(self):
        vectors = _create_test_vectors()
        result = classify_thinking_style(vectors)
        assert result in ["innovator", "developer", "consolidator"]

    def test_research_speed(self):
        result = diagnose_research_speed(6)
        assert result == "high_output"

    def test_decision_delay(self):
        result = alert_decision_delay(8)
        assert "critical" in result

    def test_undervaluation(self):
        vectors = _create_test_vectors()
        result = detect_undervaluation(vectors)
        assert isinstance(result, bool)


class TestLambda26_30:
    def test_obsidian(self):
        vectors = _create_test_vectors()
        result = restructure_for_obsidian(vectors)
        assert "obsidian_nodes" in result

    def test_notebooklm(self):
        vectors = _create_test_vectors()
        result = optimize_for_notebooklm(vectors)
        assert "audio_summaries" in result

    def test_monthly_inventory(self):
        vectors = _create_test_vectors()
        result = generate_monthly_inventory(vectors)
        assert result["status"] == "complete"

    def test_log_improvements(self):
        result = suggest_log_improvements(3)
        assert len(result) > 0

    def test_strategy_brief(self):
        vectors = _create_test_vectors()
        result = generate_monthly_strategy_brief(vectors)
        assert len(result) > 0
