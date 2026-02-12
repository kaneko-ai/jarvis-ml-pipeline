"""Behavior-focused tests for jarvis_core.scientist.coscientist."""

from __future__ import annotations

from jarvis_core.scientist.coscientist import (
    CollaboratorNetworkBuilder,
    EthicsChecker,
    ExperimentDesignerPro,
    FeasibilityAnalyzer,
    FundingOpportunityMatcher,
    HypothesisDebateSystem,
    HypothesisGenerator,
    IRBDocumentGenerator,
    LabResourceAllocator,
    LiteratureGapAnalyzer,
    MentorMatcher,
    NegativeResultPublisher,
    NoveltyScoreCalculator,
    PreregistrationGenerator,
    ReproducibilityScorer,
    ResearchImpactPredictor,
    ResearchPivotAdvisor,
    ResearchQuestionDecomposer,
    ResearchRoadmapGenerator,
    TimelineOptimizer,
    get_debate_system,
    get_experiment_designer,
    get_gap_analyzer,
    get_hypothesis_generator,
    get_question_decomposer,
)


def test_hypothesis_generator_returns_ranked_records_with_expected_keys() -> None:
    gen = HypothesisGenerator()
    gen.add_paper({"title": "Cancer pathway", "abstract": "cancer resistance", "pmid": "p1"})

    result = gen.generate_hypotheses("cancer resistance", n=4)

    assert len(result) == 4
    assert result == sorted(result, key=lambda item: item["confidence"], reverse=True)
    for item in result:
        assert set(item.keys()) == {
            "id",
            "text",
            "confidence",
            "novelty_score",
            "testability_score",
            "supporting_papers",
            "generated_at",
        }
        assert 0.4 <= item["confidence"] <= 0.9
        assert 0.3 <= item["novelty_score"] <= 0.95
        assert 0.5 <= item["testability_score"] <= 1.0



def test_hypothesis_generator_entity_extraction_and_support_fallback() -> None:
    gen = HypothesisGenerator()
    entities = gen._extract_entities("")
    assert entities["entity_a"] == "Factor A"
    assert entities["entity_b"] == "Factor B"

    text = gen._fill_template("{entity_a} may {relation} {entity_b}", entities, "topic")
    assert "Factor A" in text
    assert "influence" in text

    gen.add_paper({"title": "topic", "abstract": "topic"})
    assert gen._find_support("topic") == ["unknown"]



def test_question_decomposer_pattern_and_default_paths() -> None:
    dec = ResearchQuestionDecomposer()

    mechanism = dec.decompose("What is the mechanism of resistance?")
    assert mechanism["total"] == 3
    assert mechanism["sub_questions"][0]["id"] == "SQ1"
    assert mechanism["sub_questions"][1]["dependencies"] == ["SQ1"]

    generic = dec.decompose("Is sleep linked to productivity?")
    assert generic["total"] == 3
    assert generic["estimated_time_months"] == 18
    assert generic["sub_questions"][2]["dependencies"] == ["SQ1", "SQ2"]



def test_literature_gap_analyzer_outputs_structured_gaps_and_landscape() -> None:
    analyzer = LiteratureGapAnalyzer()
    analyzer.add_papers(
        [
            {
                "title": "Machine learning in healthcare",
                "abstract": "Longitudinal diagnosis models",
            },
            {
                "title": "Deep learning biomarkers",
                "abstract": "Validation cohort methods",
            },
        ]
    )

    gaps = analyzer.find_gaps("machine learning")
    assert [g["type"] for g in gaps] == ["under_studied", "methodological", "translational"]
    assert all(0 < g["opportunity_score"] <= 1 for g in gaps)

    landscape = analyzer.visualize_landscape()
    assert landscape["total_papers"] == 2
    assert set(landscape.keys()) == {"hot_topics", "emerging_topics", "cold_spots", "total_papers"}



def test_experiment_designer_computes_sample_size_timeline_and_budget() -> None:
    designer = ExperimentDesignerPro()
    result = designer.design_experiment("Drug X reduces tumor", variables={"expected_effect_size": 0.5})

    assert result["design"]["total_n"] == 126
    assert result["power_analysis"]["sample_size_per_group"] == 63
    assert result["statistical_analysis"]["primary"] == "t_test"
    assert result["timeline"]["total"] == "18 months"
    assert result["budget_estimate"]["total"] == 31500

    low_effect = designer.design_experiment("Drug Y", variables={"expected_effect_size": 0.2})
    assert low_effect["statistical_analysis"]["primary"] == "anova"



def test_debate_system_generates_log_and_recommendation() -> None:
    system = HypothesisDebateSystem()
    result = system.debate("Exercise improves mood", rounds=2)

    assert result["hypothesis"] == "Exercise improves mood"
    assert len(result["debate_log"]) == 6
    assert result["verdict"]["score"] == 0.72
    assert result["recommendation"] == "test"
    assert result["debate_log"][0]["agent"] == "Pro"
    assert result["debate_log"][1]["agent"] == "Con"
    assert result["debate_log"][2]["agent"] == "Moderator"



def test_research_roadmap_and_funding_outputs() -> None:
    roadmap = ResearchRoadmapGenerator().generate("Cure cancer", years=2)
    assert roadmap["duration_years"] == 2
    assert len(roadmap["milestones"]) == 2
    assert roadmap["milestones"][1]["dependencies"] == ["Year 1 completion"]

    funding = FundingOpportunityMatcher().match({"title": "Cancer"})
    assert len(funding) == 3
    assert funding[0]["source"] == "NIH Reporter"
    assert all("url" in item for item in funding)



def test_collaboration_and_impact_and_novelty() -> None:
    network = CollaboratorNetworkBuilder().build_network("Dr. Ada")
    assert network["center"] == "Dr. Ada"
    assert len(network["collaborators"]) == 2

    predictor = ResearchImpactPredictor()
    high = predictor.predict({"title": "x" * 100, "abstract": "y" * 500})
    low = predictor.predict({})
    assert high["impact_category"] == "high"
    assert low["impact_category"] == "low"

    novelty = NoveltyScoreCalculator()
    novelty.add_concepts(["quantum", "algorithm"])
    scored = novelty.score("quantum algorithm optimization")
    assert 0.0 <= scored["novelty_score"] <= 1.0
    assert "quantum" in scored["existing_concepts"]



def test_feasibility_ethics_and_irb_document() -> None:
    feasibility = FeasibilityAnalyzer().analyze({"title": "Any"})
    assert feasibility["overall_score"] == 0.74
    assert set(feasibility["factors"].keys()) == {"technical", "resource", "timeline", "expertise"}

    ethics = EthicsChecker().check("Human patient and animal genetic privacy study")
    assert ethics["requires_irb"] is True
    assert ethics["requires_iacuc"] is True
    assert ethics["privacy_considerations"] is True
    assert ethics["recommendation"] == "Consult ethics board"

    irb = IRBDocumentGenerator().generate({"title": "Clinical Trial", "sample_size": 120})
    assert "# IRB Application" in irb
    assert "Clinical Trial" in irb
    assert "120" in irb



def test_timeline_optimizer_and_resource_allocator() -> None:
    optimizer = TimelineOptimizer()
    tasks = [
        {"name": "A", "duration_months": 10, "priority": 3},
        {"name": "B", "duration_months": 20, "priority": 2},
    ]
    optimized = optimizer.optimize(tasks, {"max_months": 24})
    assert optimized["total_duration"] == 10
    assert optimized["within_constraint"] is True
    assert [t["name"] for t in optimized["scheduled_tasks"]] == ["A"]

    allocated = LabResourceAllocator().allocate(
        [{"name": "E1", "equipment_needed": 120, "personnel_needed": 250}],
        {"equipment_hours": 100, "personnel_hours": 200},
    )
    assert allocated["allocations"][0]["equipment_hours"] == 100
    assert allocated["allocations"][0]["personnel_hours"] == 200
    assert allocated["utilization"] == 0.85



def test_repro_prereg_negative_pivot_and_mentor_matcher() -> None:
    repro = ReproducibilityScorer().score({"text": "data available code available"})
    assert 0.0 <= repro["overall_score"] <= 1.0
    assert set(repro["criteria_scores"].keys()) == {
        "data_available",
        "code_available",
        "protocol_detailed",
        "reagents_described",
        "statistics_complete",
    }

    pre = PreregistrationGenerator().generate({"title": "Study", "hypothesis": "H1"})
    assert "# Study Pre-registration" in pre
    assert "Study" in pre

    neg = NegativeResultPublisher().format({"topic": "Biomarker"})
    assert neg["title"].startswith("Null findings: Biomarker")
    assert "target_journals" in neg and len(neg["target_journals"]) == 3

    pivot = ResearchPivotAdvisor().advise({}, "goal")
    assert pivot["continue_current"]["recommendation"] == "Proceed with modifications"
    assert len(pivot["pivot_options"]) == 3

    mentors = [
        {"name": f"m{i}", "expertise": ["ai", "bio"] if i % 2 == 0 else ["chem"]}
        for i in range(7)
    ]
    matches = MentorMatcher().match({"interests": ["ai", "bio"]}, mentors)
    assert len(matches) == 4
    assert matches == sorted(matches, key=lambda item: item["match_score"], reverse=True)



def test_factory_functions_return_expected_instances() -> None:
    hypothesis_generator = get_hypothesis_generator()
    question_decomposer = get_question_decomposer()
    gap_analyzer = get_gap_analyzer()
    experiment_designer = get_experiment_designer()
    debate_system = get_debate_system()

    assert isinstance(hypothesis_generator, HypothesisGenerator)
    assert isinstance(question_decomposer, ResearchQuestionDecomposer)
    assert isinstance(gap_analyzer, LiteratureGapAnalyzer)
    assert isinstance(experiment_designer, ExperimentDesignerPro)
    assert isinstance(debate_system, HypothesisDebateSystem)

    assert callable(hypothesis_generator.generate_hypotheses)
    assert callable(question_decomposer.decompose)
    assert callable(gap_analyzer.find_gaps)
    assert callable(experiment_designer.design_experiment)
    assert callable(debate_system.debate)
