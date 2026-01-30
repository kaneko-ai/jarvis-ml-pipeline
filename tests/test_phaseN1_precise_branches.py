"""Phase N-1: Precise Branch Coverage for stages/summarization_scoring.py.

Strategy: Create proper TaskContext and Artifacts, call each stage function with correct inputs
to ensure all branches are covered.
"""

from unittest.mock import patch


class TestSummarizationMultigrain:
    """Test stage_summarization_multigrain - lines 23-56."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_papers_short_text(self, mock_log):
        """Cover lines 26-27 (short text branch)."""
        from jarvis_core.stages.summarization_scoring import stage_summarization_multigrain
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()

        # Paper with short abstract (< 300 chars)
        paper = Paper(doc_id="p1", title="Short Paper", abstract="Short abstract")
        artifacts.papers = [paper]

        result = stage_summarization_multigrain(context, artifacts)
        assert "p1" in result.summaries
        assert result.summaries["p1"] == "Short abstract"  # No truncation

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_papers_long_text(self, mock_log):
        """Cover lines 30-32 (long text truncation branch)."""
        from jarvis_core.stages.summarization_scoring import stage_summarization_multigrain
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()

        # Paper with long abstract (> 1000 chars)
        long_text = "A" * 1500
        paper = Paper(doc_id="p2", title="Long Paper", abstract=long_text)
        artifacts.papers = [paper]

        result = stage_summarization_multigrain(context, artifacts)
        assert "p2" in result.summaries
        assert "..." in result.summaries["p2"]  # Truncated
        assert len(result.summaries["p2"]) <= 304  # 300 + "..."


class TestSummarizationBeginner:
    """Test stage_summarization_beginner - lines 59-93."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_scientific_terms(self, mock_log):
        """Cover lines 68-72 (term replacement)."""
        from jarvis_core.stages.summarization_scoring import stage_summarization_beginner
        from jarvis_core.contracts.types import TaskContext, Artifacts

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.summaries = {"doc1": "This involves apoptosis and in vitro studies"}

        result = stage_summarization_beginner(context, artifacts)
        beginner_text = result.metadata.get("doc1_beginner", "")
        assert "細胞の自然死" in beginner_text
        assert "試験管内" in beginner_text


class TestSummarizationCompare:
    """Test stage_summarization_compare - lines 96-125."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_two_or_more_papers(self, mock_log):
        """Cover lines 99-104 (comparison branch)."""
        from jarvis_core.stages.summarization_scoring import stage_summarization_compare
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.papers = [
            Paper(doc_id="p1", title="Paper 1"),
            Paper(doc_id="p2", title="Paper 2"),
        ]

        result = stage_summarization_compare(context, artifacts)
        assert "comparison" in result.metadata
        assert "p1" in result.metadata["comparison"]["papers_compared"]

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_single_paper(self, mock_log):
        """Cover line 99 (False branch - fewer than 2 papers)."""
        from jarvis_core.stages.summarization_scoring import stage_summarization_compare
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.papers = [Paper(doc_id="p1", title="Paper 1")]

        result = stage_summarization_compare(context, artifacts)
        assert "comparison" not in result.metadata


class TestSummarizationReproducibility:
    """Test stage_summarization_reproducibility - lines 128-159."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_methods(self, mock_log):
        """Cover lines 133-138 (with methods)."""
        from jarvis_core.stages.summarization_scoring import stage_summarization_reproducibility
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.papers = [Paper(doc_id="p1", title="Paper 1")]
        artifacts.metadata["methods"] = [{"doc_id": "p1", "method": "PCR"}]

        result = stage_summarization_reproducibility(context, artifacts)
        repro = result.metadata.get("p1_reproducibility", {})
        assert repro.get("reproducibility_score") == 0.7

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_without_methods(self, mock_log):
        """Cover line 137 (else branch - no methods)."""
        from jarvis_core.stages.summarization_scoring import stage_summarization_reproducibility
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.papers = [Paper(doc_id="p1", title="Paper 1")]

        result = stage_summarization_reproducibility(context, artifacts)
        repro = result.metadata.get("p1_reproducibility", {})
        assert repro.get("reproducibility_score") == 0.3


class TestSummarizationRefutable:
    """Test stage_summarization_refutable - lines 162-191."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_fact_claims_and_evidence(self, mock_log):
        """Cover lines 165-170 (claim_type == 'fact' with evidence)."""
        from jarvis_core.stages.summarization_scoring import stage_summarization_refutable
        from jarvis_core.contracts.types import TaskContext, Artifacts, Claim, EvidenceLink

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()

        claim = Claim(
            claim_id="c1",
            claim_text="Test claim",
            claim_type="fact",
            evidence=[
                EvidenceLink(
                    doc_id="p1", section="intro", chunk_id="ch1", start=0, end=10, confidence=0.9
                )
            ],
        )
        artifacts.claims = [claim]

        result = stage_summarization_refutable(context, artifacts)
        ref = result.metadata.get("c1_refutable", {})
        assert ref.get("is_refutable")
        assert ref.get("evidence_count") == 1

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_fact_claims_no_evidence(self, mock_log):
        """Cover lines 168-169 (fact claim with no evidence)."""
        from jarvis_core.stages.summarization_scoring import stage_summarization_refutable
        from jarvis_core.contracts.types import TaskContext, Artifacts, Claim

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()

        claim = Claim(claim_id="c1", claim_text="Test claim", claim_type="fact", evidence=[])
        artifacts.claims = [claim]

        result = stage_summarization_refutable(context, artifacts)
        ref = result.metadata.get("c1_refutable", {})
        assert not ref.get("is_refutable")

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_non_fact_claims(self, mock_log):
        """Cover line 166 (claim_type != 'fact')."""
        from jarvis_core.stages.summarization_scoring import stage_summarization_refutable
        from jarvis_core.contracts.types import TaskContext, Artifacts, Claim

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()

        claim = Claim(claim_id="c1", claim_text="Test claim", claim_type="log", evidence=[])
        artifacts.claims = [claim]

        result = stage_summarization_refutable(context, artifacts)
        assert "c1_refutable" not in result.metadata


class TestScoringImportance:
    """Test stage_scoring_importance - lines 199-236."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_novel_and_significant(self, mock_log):
        """Cover lines 206-209 (all keyword branches)."""
        from jarvis_core.stages.summarization_scoring import stage_scoring_importance
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.papers = [
            Paper(
                doc_id="p1",
                title="Novel Approach",
                abstract="This novel and significant study is the first of its kind",
            )
        ]

        result = stage_scoring_importance(context, artifacts)
        score = result.scores.get("p1_importance")
        assert score.value >= 0.85  # 0.5 + 0.2 + 0.15

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_without_keywords(self, mock_log):
        """Cover base score without keywords."""
        from jarvis_core.stages.summarization_scoring import stage_scoring_importance
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.papers = [
            Paper(doc_id="p1", title="Regular Paper", abstract="A regular study about something")
        ]

        result = stage_scoring_importance(context, artifacts)
        score = result.scores.get("p1_importance")
        assert score.value == 0.5


class TestScoringBiasRisk:
    """Test stage_scoring_bias_risk - lines 275-312."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_all_risk_modifiers(self, mock_log):
        """Cover lines 282-287 (all risk branches)."""
        from jarvis_core.stages.summarization_scoring import stage_scoring_bias_risk
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()

        # Low risk: randomized control study
        artifacts.papers = [
            Paper(
                doc_id="p1",
                title="RCT",
                abstract="This randomized control trial was funded by government",
            )
        ]

        result = stage_scoring_bias_risk(context, artifacts)
        score = result.scores.get("p1_bias_risk")
        # 0.3 - 0.1 (randomized) - 0.1 (control) + 0.2 (funded by) = 0.3
        assert score.value == 0.3


class TestScoringEvidenceTier:
    """Test stage_scoring_evidence_tier - lines 315-352."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_known_study_type(self, mock_log):
        """Cover lines 326-330."""
        from jarvis_core.stages.summarization_scoring import stage_scoring_evidence_tier
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.papers = [Paper(doc_id="p1", title="Meta Analysis")]
        artifacts.metadata["p1_study_type"] = "meta-analysis"

        result = stage_scoring_evidence_tier(context, artifacts)
        score = result.scores.get("p1_evidence_tier")
        assert score.value == 1.0

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_unknown_study_type(self, mock_log):
        """Cover line 327 (default value)."""
        from jarvis_core.stages.summarization_scoring import stage_scoring_evidence_tier
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.papers = [Paper(doc_id="p1", title="Unknown Study")]

        result = stage_scoring_evidence_tier(context, artifacts)
        score = result.scores.get("p1_evidence_tier")
        assert score.value == 0.5


class TestScoringClinicalRelevance:
    """Test stage_scoring_clinical_relevance - lines 355-392."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_clinical_keywords(self, mock_log):
        """Cover lines 362-365."""
        from jarvis_core.stages.summarization_scoring import stage_scoring_clinical_relevance
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.papers = [
            Paper(
                doc_id="p1",
                title="Clinical Trial",
                abstract="Patient treatment and therapy outcomes",
            )
        ]

        result = stage_scoring_clinical_relevance(context, artifacts)
        score = result.scores.get("p1_clinical_relevance")
        assert score.value >= 0.8  # 0.3 + 0.3 + 0.2


class TestScoringPersonalFit:
    """Test stage_scoring_personal_fit - lines 395-429."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_high_overlap(self, mock_log):
        """Cover lines 398-406."""
        from jarvis_core.stages.summarization_scoring import stage_scoring_personal_fit
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="machine learning cancer")
        artifacts = Artifacts()
        artifacts.papers = [Paper(doc_id="p1", title="Machine Learning Cancer Detection")]

        result = stage_scoring_personal_fit(context, artifacts)
        score = result.scores.get("p1_personal_fit")
        assert score.value > 0.5


class TestScoringLearningROI:
    """Test stage_scoring_learning_roi - lines 432-467."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_existing_scores(self, mock_log):
        """Cover lines 436-442."""
        from jarvis_core.stages.summarization_scoring import stage_scoring_learning_roi
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper, Score

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.papers = [Paper(doc_id="p1", title="Test Paper")]
        artifacts.scores["p1_importance"] = Score(name="importance", value=0.8, explanation="test")
        artifacts.scores["p1_personal_fit"] = Score(
            name="personal_fit", value=0.6, explanation="test"
        )

        result = stage_scoring_learning_roi(context, artifacts)
        score = result.scores.get("p1_learning_roi")
        assert score.value == 0.7  # (0.8 + 0.6) / 2

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_without_existing_scores(self, mock_log):
        """Cover lines 439-440 (default values)."""
        from jarvis_core.stages.summarization_scoring import stage_scoring_learning_roi
        from jarvis_core.contracts.types import TaskContext, Artifacts, Paper

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.papers = [Paper(doc_id="p1", title="Test Paper")]

        result = stage_scoring_learning_roi(context, artifacts)
        score = result.scores.get("p1_learning_roi")
        assert score.value == 0.5  # (0.5 + 0.5) / 2


class TestDesignGapAnalysis:
    """Test stage_design_gap_analysis - lines 615-651."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_limitations(self, mock_log):
        """Cover lines 619-628."""
        from jarvis_core.stages.summarization_scoring import stage_design_gap_analysis
        from jarvis_core.contracts.types import TaskContext, Artifacts

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.metadata["limitations"] = [
            {"limitation": "Small sample size"},
            {"limitation": "Short follow-up"},
        ]

        result = stage_design_gap_analysis(context, artifacts)
        gaps = result.metadata.get("gaps", [])
        assert len(gaps) == 2

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_without_limitations(self, mock_log):
        """Cover empty limitations."""
        from jarvis_core.stages.summarization_scoring import stage_design_gap_analysis
        from jarvis_core.contracts.types import TaskContext, Artifacts

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()

        result = stage_design_gap_analysis(context, artifacts)
        gaps = result.metadata.get("gaps", [])
        assert len(gaps) == 0


class TestDesignNextExperiments:
    """Test stage_design_next_experiments - lines 654-692."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_gaps(self, mock_log):
        """Cover lines 660-668."""
        from jarvis_core.stages.summarization_scoring import stage_design_next_experiments
        from jarvis_core.contracts.types import TaskContext, Artifacts

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.metadata["gaps"] = [
            {"gap_id": "g1", "description": "Need more data"},
            {"gap_id": "g2", "description": "Need longer follow-up"},
        ]

        result = stage_design_next_experiments(context, artifacts)
        proposals = result.metadata.get("experiment_proposals", [])
        assert len(proposals) == 2


class TestDesignProtocolDraft:
    """Test stage_design_protocol_draft - lines 695-732."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_proposals(self, mock_log):
        """Cover lines 701-709."""
        from jarvis_core.stages.summarization_scoring import stage_design_protocol_draft
        from jarvis_core.contracts.types import TaskContext, Artifacts

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.metadata["experiment_proposals"] = [
            {"proposal_id": "exp1", "title": "Experiment 1"},
            {"proposal_id": "exp2", "title": "Experiment 2"},
        ]

        result = stage_design_protocol_draft(context, artifacts)
        protocols = result.metadata.get("protocols", [])
        assert len(protocols) == 2


class TestDesignStatsDesign:
    """Test stage_design_stats_design - lines 735-773."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_proposals(self, mock_log):
        """Cover lines 741-750."""
        from jarvis_core.stages.summarization_scoring import stage_design_stats_design
        from jarvis_core.contracts.types import TaskContext, Artifacts

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.metadata["experiment_proposals"] = [
            {"proposal_id": "exp1"},
            {"proposal_id": "exp2"},
        ]

        result = stage_design_stats_design(context, artifacts)
        stats = result.metadata.get("stats_designs", [])
        assert len(stats) == 2


class TestDesignRiskDiagnosis:
    """Test stage_design_risk_diagnosis - lines 776-813."""

    @patch("jarvis_core.stages.summarization_scoring.log_audit")
    def test_with_proposals(self, mock_log):
        """Cover lines 782-788."""
        from jarvis_core.stages.summarization_scoring import stage_design_risk_diagnosis
        from jarvis_core.contracts.types import TaskContext, Artifacts

        context = TaskContext(goal="test goal")
        artifacts = Artifacts()
        artifacts.metadata["experiment_proposals"] = [
            {"proposal_id": "exp1"},
        ]

        result = stage_design_risk_diagnosis(context, artifacts)
        risks = result.metadata.get("risk_diagnoses", [])
        assert len(risks) == 1