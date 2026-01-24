"""Tests for Phase Ψ (Research OS v3.0 Core).

Tests Ψ-1 to Ψ-30 modules.
"""

from jarvis_core.experimental.career_engines import (
    monitor_burnout_risk,
    plan_international_mobility,
    simulate_reputation_trajectory,
    suggest_mentor_profile,
    track_skill_gap,
)
from jarvis_core.experimental.clinical_readiness import assess_clinical_readiness
from jarvis_core.experimental.funding_cliff import predict_funding_cliff
from jarvis_core.kill_switch import recommend_kill_switch
from jarvis_core.experimental.lab_culture import detect_lab_culture_risk
from jarvis_core.experimental.lab_to_startup import translate_to_startup
from jarvis_core.logic_citation import (
    calculate_citation_power,
    calculate_claim_confidence,
    generate_argument_map,
    predict_paper_longevity,
    track_controversies,
)
from jarvis_core.meta_science import (
    detect_citation_cartel,
    observe_meta_science,
    predict_field_collapse,
    suggest_self_evolution,
    track_journal_power_shift,
)
from jarvis_core.experimental.negative_results import (
    NegativeResult,
    NegativeResultsVault,
    analyze_negative_results,
)
from jarvis_core.paper_vector import (
    BiologicalAxisVector,
    ConceptVector,
    ImpactVector,
    MetadataVector,
    MethodVector,
    PaperVector,
    TemporalVector,
)
from jarvis_core.experimental.pi_succession import plan_pi_succession
from jarvis_core.experimental.reproducibility_cert import certify_reproducibility
from jarvis_core.experimental.roi_engine import calculate_research_roi
from jarvis_core.experimental.student_portfolio import analyze_student_portfolio
from jarvis_core.thinking_engines import (
    analyze_counterfactual,
    discover_blind_spots,
    simulate_concept_mutation,
    simulate_hypothesis_evolution,
    simulate_research_debate,
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
            metadata=MetadataVector(year=2018, species=["mouse"]),
            concept=ConceptVector(concepts={"CD73": 0.9}),
            method=MethodVector(methods={"Western blot": 0.8}),
            biological_axis=BiologicalAxisVector(immune_activation=-0.5),
            temporal=TemporalVector(novelty=0.4),
            impact=ImpactVector(future_potential=0.3),
        ),
        PaperVector(
            paper_id="p2",
            source_locator="pdf:2.pdf",
            metadata=MetadataVector(year=2022, species=["human"]),
            concept=ConceptVector(concepts={"PD-1": 0.8}),
            method=MethodVector(methods={"scRNA-seq": 0.9}),
            biological_axis=BiologicalAxisVector(immune_activation=0.6),
            temporal=TemporalVector(novelty=0.8),
            impact=ImpactVector(future_potential=0.7),
        ),
    ]


class TestROIEngine:
    def test_calculates_roi(self):
        vectors = _create_test_vectors()
        result = calculate_research_roi(vectors, 12)
        assert "roi_score" in result
        assert 0 <= result["roi_score"] <= 1

    def test_empty_input(self):
        result = calculate_research_roi([], 12)
        assert result["roi_score"] == 0.0


class TestNegativeResults:
    def test_vault_operations(self):
        vault = NegativeResultsVault()
        vault.add(
            NegativeResult(
                id="1", hypothesis="H1", experiment="E1", outcome="failed", failure_type="technical"
            )
        )
        assert len(vault.results) == 1

    def test_analyze(self):
        results = [
            NegativeResult(
                id="1", hypothesis="H1", experiment="E1", outcome="failed", failure_type="technical"
            )
        ]
        analysis = analyze_negative_results(results)
        assert analysis["total"] == 1


class TestReproducibilityCert:
    def test_certifies(self):
        vectors = _create_test_vectors()
        result = certify_reproducibility("CD73 hypothesis", vectors)
        assert "reproducibility_score" in result
        assert result["estimated"] is True


class TestLabToStartup:
    def test_translates(self):
        vectors = _create_test_vectors()
        result = translate_to_startup(vectors)
        assert "startup_hypothesis" in result
        assert "moat_reason" in result


class TestClinicalReadiness:
    def test_assesses(self):
        vectors = _create_test_vectors()
        result = assess_clinical_readiness(vectors)
        assert 0 <= result["readiness_level"] <= 5


class TestStudentPortfolio:
    def test_analyzes(self):
        vectors = _create_test_vectors()
        result = analyze_student_portfolio({"student1": vectors})
        assert len(result) == 1
        assert "risk_rank" in result[0]


class TestKillSwitch:
    def test_recommends(self):
        vectors = _create_test_vectors()
        result = recommend_kill_switch("theme1", vectors)
        assert result["recommendation"] in ["continue", "pivot", "stop"]


class TestLabCulture:
    def test_detects(self):
        vectors = _create_test_vectors()
        result = detect_lab_culture_risk(vectors)
        assert "culture_risk_index" in result


class TestPISuccession:
    def test_plans(self):
        vectors = _create_test_vectors()
        result = plan_pi_succession(vectors)
        assert "future_theme_map" in result


class TestFundingCliff:
    def test_predicts(self):
        vectors = _create_test_vectors()
        result = predict_funding_cliff(vectors, 24)
        assert "months_to_cliff" in result


class TestLogicCitation:
    def test_argument_map(self):
        result = generate_argument_map(["claim1", "claim2"])
        assert len(result["nodes"]) == 2

    def test_controversies(self):
        vectors = _create_test_vectors()
        result = track_controversies(vectors)
        assert isinstance(result, list)

    def test_claim_confidence(self):
        vectors = _create_test_vectors()
        result = calculate_claim_confidence("CD73", vectors)
        assert result["estimated"] is True

    def test_citation_power(self):
        vectors = _create_test_vectors()
        result = calculate_citation_power(vectors)
        assert "citation_strength" in result

    def test_longevity(self):
        vectors = _create_test_vectors()
        result = predict_paper_longevity(vectors[0])
        assert result["estimated"] is True


class TestThinkingEngines:
    def test_counterfactual(self):
        vectors = _create_test_vectors()
        result = analyze_counterfactual(vectors[0], vectors)
        assert "impact_delta" in result

    def test_blind_spots(self):
        vectors = _create_test_vectors()
        result = discover_blind_spots(vectors)
        assert isinstance(result, list)

    def test_concept_mutation(self):
        vectors = _create_test_vectors()
        result = simulate_concept_mutation("CD73", vectors)
        assert "mutation_paths" in result

    def test_debate(self):
        vectors = _create_test_vectors()
        result = simulate_research_debate("hypothesis", vectors)
        assert result["winner"] in ["pro", "con"]

    def test_darwinism(self):
        vectors = _create_test_vectors()
        result = simulate_hypothesis_evolution(["H1", "H2"], vectors)
        assert "surviving_hypotheses" in result


class TestCareerEngines:
    def test_burnout(self):
        vectors = _create_test_vectors()
        result = monitor_burnout_risk(vectors, 60, 18)
        assert 0 <= result["burnout_risk"] <= 1

    def test_skill_gap(self):
        vectors = _create_test_vectors()
        result = track_skill_gap(vectors, ["CRISPR"])
        assert "skill_gap_timeline" in result

    def test_mentor(self):
        vectors = _create_test_vectors()
        result = suggest_mentor_profile(vectors)
        assert "mentor_profile" in result

    def test_mobility(self):
        vectors = _create_test_vectors()
        result = plan_international_mobility(vectors)
        assert "preparation_steps" in result

    def test_reputation(self):
        vectors = _create_test_vectors()
        result = simulate_reputation_trajectory(vectors, 3)
        assert len(result["reputation_curve"]) == 4


class TestMetaScience:
    def test_field_collapse(self):
        vectors = _create_test_vectors()
        result = predict_field_collapse(vectors, "CD73")
        assert "collapse_risk" in result

    def test_journal_power(self):
        vectors = _create_test_vectors()
        result = track_journal_power_shift(vectors)
        assert "power_shift_map" in result

    def test_citation_cartel(self):
        vectors = _create_test_vectors()
        result = detect_citation_cartel(vectors)
        assert "cartel_clusters" in result

    def test_meta_science(self):
        vectors = _create_test_vectors()
        result = observe_meta_science(vectors)
        assert "system_metrics" in result

    def test_self_evolution(self):
        vectors = _create_test_vectors()
        result = suggest_self_evolution(vectors, ["feature1"])
        assert "next_feature_candidates" in result
