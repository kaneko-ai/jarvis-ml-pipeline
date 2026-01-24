"""Tests for Phase ﾎ｣ (Extended Research Analysis).

Tests ﾎ｣-1 to ﾎ｣-30 modules.
"""

from jarvis_core.paper_vector import (
    BiologicalAxisVector,
    ConceptVector,
    ImpactVector,
    MetadataVector,
    MethodVector,
    PaperVector,
    TemporalVector,
)
from jarvis_core.experimental.sigma_modules import (
    analyze_cluster_dynamics,
    analyze_hypothesis_dependencies,
    assess_field_saturation,
    assess_reproducibility_risk,
    # ﾎ｣-8縲慚｣-13
    build_impact_heatmap,
    check_sample_size,
    check_supplement_completeness,
    detect_citation_bias,
    detect_consensus,
    detect_discussion_gaps,
    detect_new_concepts,
    # ﾎ｣-26縲慚｣-30
    detect_research_drift,
    enumerate_controls,
    estimate_hypothesis_lifetime,
    explain_model_reasoning,
    find_counter_evidence,
    flag_risky_sentences,
    generate_hypothesis_diagram,
    generate_negative_hypothesis,
    generate_periodic_review,
    infer_causal_direction,
    map_journal_trends,
    map_method_failures,
    map_research_density,
    # ﾎ｣-20縲慚｣-25
    plan_figures,
    # ﾎ｣-1縲慚｣-7
    score_hypothesis,
    # ﾎ｣-14縲慚｣-19
    score_protocol_difficulty,
    structure_graphical_abstract,
    sync_research_log,
    validate_stats_method,
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
            metadata=MetadataVector(year=2018),
            concept=ConceptVector(concepts={"CD73": 0.9}),
            method=MethodVector(methods={"Western blot": 0.8}),
            biological_axis=BiologicalAxisVector(immune_activation=-0.5),
            temporal=TemporalVector(novelty=0.4),
            impact=ImpactVector(future_potential=0.3),
        ),
        PaperVector(
            paper_id="p2",
            source_locator="pdf:2.pdf",
            metadata=MetadataVector(year=2022),
            concept=ConceptVector(concepts={"PD-1": 0.8, "CD73": 0.3}),
            method=MethodVector(methods={"scRNA-seq": 0.9}),
            biological_axis=BiologicalAxisVector(immune_activation=0.6),
            temporal=TemporalVector(novelty=0.8),
            impact=ImpactVector(future_potential=0.7),
        ),
    ]

class TestSigma1_7:
    """諤晁・・莉ｮ隱ｬ邉ｻ (ﾎ｣-1縲慚｣-7)."""

    def test_score_hypothesis(self):
        vectors = _create_test_vectors()
        result = score_hypothesis("CD73 function", vectors)
        assert "score" in result
        assert result["estimated"] is True

    def test_hypothesis_dependencies(self):
        deps = analyze_hypothesis_dependencies(["CD73 regulates X", "CD73 inhibits Y"], [])
        assert isinstance(deps, list)

    def test_negative_hypothesis(self):
        neg = generate_negative_hypothesis("CD73 is important")
        assert "not" in neg.lower()

    def test_hypothesis_lifetime(self):
        vectors = _create_test_vectors()
        result = estimate_hypothesis_lifetime("test", vectors)
        assert result["years_remaining"] >= 1

    def test_detect_consensus(self):
        vectors = _create_test_vectors()
        result = detect_consensus(vectors, "CD73")
        assert "consensus" in result

    def test_counter_evidence(self):
        vectors = _create_test_vectors()
        counters = find_counter_evidence("immune activation", vectors)
        assert isinstance(counters, list)

    def test_hypothesis_diagram(self):
        diagram = generate_hypothesis_diagram(["H1", "H2"])
        assert "nodes" in diagram

class TestSigma8_13:
    """蛻・梵繝ｻ蜿ｯ隕門喧邉ｻ (ﾎ｣-8縲慚｣-13)."""

    def test_impact_heatmap(self):
        vectors = _create_test_vectors()
        heatmap = build_impact_heatmap(vectors)
        assert isinstance(heatmap, dict)

    def test_cluster_dynamics(self):
        vectors = _create_test_vectors()
        dynamics = analyze_cluster_dynamics(vectors)
        assert len(dynamics) > 0

    def test_causal_direction(self):
        vectors = _create_test_vectors()
        result = infer_causal_direction("CD73", "PD-1", vectors)
        assert result["estimated"] is True

    def test_method_failures(self):
        vectors = _create_test_vectors()
        failures = map_method_failures(vectors)
        assert isinstance(failures, dict)

    def test_journal_trends(self):
        vectors = _create_test_vectors()
        trends = map_journal_trends(vectors)
        assert isinstance(trends, dict)

    def test_research_density(self):
        vectors = _create_test_vectors()
        density = map_research_density(vectors)
        assert isinstance(density, dict)

class TestSigma14_19:
    """螳滄ｨ薙・險ｭ險育ｳｻ (ﾎ｣-14縲慚｣-19)."""

    def test_protocol_difficulty(self):
        score = score_protocol_difficulty(["scRNA-seq", "qPCR"])
        assert 0 <= score <= 1

    def test_reproducibility_risk(self):
        vectors = _create_test_vectors()
        risk = assess_reproducibility_risk(vectors)
        assert 0 <= risk["risk"] <= 1

    def test_enumerate_controls(self):
        controls = enumerate_controls("knockout")
        assert len(controls) >= 2

    def test_sample_size(self):
        result = check_sample_size(20)
        assert "adequate" in result

    def test_stats_method(self):
        method = validate_stats_method("continuous", "two_groups")
        assert len(method) > 0

    def test_model_reasoning(self):
        vectors = _create_test_vectors()
        reasoning = explain_model_reasoning("mouse", vectors)
        assert len(reasoning) > 0

class TestSigma20_25:
    """隲匁枚繝ｻ逋ｺ陦ｨ陬懷勧 (ﾎ｣-20縲慚｣-25)."""

    def test_plan_figures(self):
        vectors = _create_test_vectors()
        figures = plan_figures(vectors)
        assert len(figures) >= 2

    def test_graphical_abstract(self):
        structure = structure_graphical_abstract()
        assert "sections" in structure

    def test_supplement_check(self):
        missing = check_supplement_completeness(["methods_detail"])
        assert "raw_data" in missing

    def test_discussion_gaps(self):
        gaps = detect_discussion_gaps(["CD73 is key"], "The paper discusses PD-1")
        assert len(gaps) > 0

    def test_risky_sentences(self):
        flagged = flag_risky_sentences(["This proves the hypothesis"])
        assert len(flagged) > 0

    def test_citation_bias(self):
        vectors = _create_test_vectors()
        bias = detect_citation_bias(vectors)
        assert "recency_bias" in bias

class TestSigma26_30:
    """邯咏ｶ壹・驕狗畑邉ｻ (ﾎ｣-26縲慚｣-30)."""

    def test_research_drift(self):
        old = _create_test_vectors()[:1]
        new = _create_test_vectors()
        drift = detect_research_drift(old, new)
        assert "drift_detected" in drift

    def test_periodic_review(self):
        vectors = _create_test_vectors()
        review = generate_periodic_review(vectors)
        assert review["period"] == "quarterly"

    def test_field_saturation(self):
        vectors = _create_test_vectors()
        sat = assess_field_saturation(vectors, "CD73")
        assert 0 <= sat["saturation"] <= 1

    def test_new_concepts(self):
        old = _create_test_vectors()[:1]
        new = _create_test_vectors()
        new_concepts = detect_new_concepts(old, new)
        assert isinstance(new_concepts, list)

    def test_sync_log(self):
        vectors = _create_test_vectors()
        status = sync_research_log(vectors)
        assert status["sync_status"] == "complete"
