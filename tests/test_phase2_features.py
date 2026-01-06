"""Tests for Phase 2 Differentiating Features.

Tests for Task 2.1-2.3:
- Evidence Grading (GRADE)
- Citation Stance Analysis
- Contradiction Detection
"""
import pytest


class TestGRADESystem:
    """Tests for GRADE evidence grading."""

    def test_grade_levels(self):
        """Test GRADELevel enum."""
        from jarvis_core.analysis.grade_system import GRADELevel
        
        assert GRADELevel.HIGH.value == "high"
        assert GRADELevel.VERY_LOW.value == "very_low"

    def test_study_design_enum(self):
        """Test StudyDesign enum."""
        from jarvis_core.analysis.grade_system import StudyDesign
        
        assert StudyDesign.RCT.value == "rct"
        assert StudyDesign.SYSTEMATIC_REVIEW.value == "systematic_review"

    def test_rule_based_grader_rct_detection(self):
        """Test RCT study design detection."""
        from jarvis_core.analysis.grade_system import RuleBasedGrader, StudyDesign
        
        grader = RuleBasedGrader()
        
        text = "This randomized controlled trial enrolled 500 patients..."
        design = grader.detect_study_design(text)
        
        assert design == StudyDesign.RCT

    def test_rule_based_grader_observational_detection(self):
        """Test observational study detection."""
        from jarvis_core.analysis.grade_system import RuleBasedGrader, StudyDesign
        
        grader = RuleBasedGrader()
        
        text = "This prospective cohort study followed participants..."
        design = grader.detect_study_design(text)
        
        assert design == StudyDesign.OBSERVATIONAL

    def test_grade_assessment_dataclass(self):
        """Test GRADEAssessment dataclass."""
        from jarvis_core.analysis.grade_system import (
            GRADEAssessment, GRADELevel, StudyDesign
        )
        
        assessment = GRADEAssessment(
            evidence_id="ev1",
            claim_id="c1",
            initial_level=GRADELevel.HIGH,
            study_design=StudyDesign.RCT,
            final_level=GRADELevel.MODERATE,
            confidence_score=0.75,
        )
        
        d = assessment.to_dict()
        assert d["final_level"] == "moderate"
        assert d["confidence_score"] == 0.75

    def test_ensemble_grader_grade(self):
        """Test ensemble grader."""
        from jarvis_core.analysis.grade_system import EnsembleGrader
        
        grader = EnsembleGrader(use_llm=False)
        
        result = grader.grade(
            evidence_id="ev1",
            claim_id="c1",
            claim_text="Drug X reduces symptoms",
            evidence_text="This double-blind randomized trial showed significant effects",
        )
        
        assert result.evidence_id == "ev1"
        assert result.confidence_score > 0

    def test_grade_batch(self):
        """Test batch grading."""
        from jarvis_core.analysis.grade_system import grade_evidence_with_grade
        
        claims = [{"claim_id": "c1", "claim_text": "Test claim"}]
        evidence = [{"evidence_id": "e1", "claim_id": "c1", "text": "RCT showed..."}]
        
        assessments, stats = grade_evidence_with_grade(evidence, claims, use_llm=False)
        
        assert len(assessments) == 1
        assert "total_evidence" in stats


class TestCitationStance:
    """Tests for citation stance analysis."""

    def test_citation_stance_enum(self):
        """Test CitationStance enum."""
        from jarvis_core.analysis.citation_stance import CitationStance
        
        assert CitationStance.SUPPORTS.value == "supports"
        assert CitationStance.CONTRADICTS.value == "contradicts"

    def test_stance_result_dataclass(self):
        """Test StanceResult dataclass."""
        from jarvis_core.analysis.citation_stance import StanceResult, CitationStance
        
        result = StanceResult(
            claim_id="c1",
            evidence_id="e1",
            stance=CitationStance.SUPPORTS,
            confidence=0.8,
            explanation="Test",
            cue_words=["confirms"],
        )
        
        d = result.to_dict()
        assert d["stance"] == "supports"

    def test_rule_classifier_support(self):
        """Test support detection."""
        from jarvis_core.analysis.citation_stance import (
            RuleBasedStanceClassifier, CitationStance
        )
        
        classifier = RuleBasedStanceClassifier()
        
        result = classifier.classify(
            claim_text="Drug X is effective",
            evidence_text="Our study confirms that Drug X shows significant efficacy",
        )
        
        assert result.stance == CitationStance.SUPPORTS
        assert "confirm" in result.cue_words[0].lower()

    def test_rule_classifier_contradiction(self):
        """Test contradiction detection."""
        from jarvis_core.analysis.citation_stance import (
            RuleBasedStanceClassifier, CitationStance
        )
        
        classifier = RuleBasedStanceClassifier()
        
        result = classifier.classify(
            claim_text="Drug X is effective",
            evidence_text="However, our study failed to find any effect of Drug X",
        )
        
        assert result.stance == CitationStance.CONTRADICTS

    def test_ensemble_classifier(self):
        """Test ensemble stance classifier."""
        from jarvis_core.analysis.citation_stance import EnsembleStanceClassifier
        
        classifier = EnsembleStanceClassifier(use_llm=False)
        
        result = classifier.classify(
            claim_text="Test claim",
            evidence_text="This study supports the hypothesis",
        )
        
        assert result.stance is not None

    def test_analyze_citations_batch(self):
        """Test batch citation analysis."""
        from jarvis_core.analysis.citation_stance import analyze_citations
        
        claims = [{"claim_id": "c1", "text": "Test claim"}]
        evidence = [
            {"evidence_id": "e1", "claim_id": "c1", "text": "Confirms the claim"},
            {"evidence_id": "e2", "claim_id": "c1", "text": "Contradicts the claim"},
        ]
        
        results, stats = analyze_citations(claims, evidence, use_llm=False)
        
        assert len(results) == 2
        assert "stance_distribution" in stats


class TestContradictionDetector:
    """Tests for contradiction detection."""

    def test_contradiction_dataclass(self):
        """Test Contradiction dataclass."""
        from jarvis_core.analysis.contradiction_detector import Contradiction
        
        c = Contradiction(
            evidence_id_1="e1",
            evidence_id_2="e2",
            claim_id="c1",
            contradiction_type="direct",
            confidence=0.8,
            explanation="Opposing stances",
            severity="high",
        )
        
        d = c.to_dict()
        assert d["evidence_pair"] == ["e1", "e2"]
        assert d["severity"] == "high"

    def test_stance_based_contradiction(self):
        """Test stance-based contradiction detection."""
        from jarvis_core.analysis.contradiction_detector import ContradictionDetector
        
        detector = ContradictionDetector()
        
        stance_results = [
            {"evidence_id": "e1", "claim_id": "c1", "stance": "supports", "confidence": 0.8},
            {"evidence_id": "e2", "claim_id": "c1", "stance": "contradicts", "confidence": 0.7},
        ]
        
        contradictions = detector.detect_stance_contradictions(stance_results)
        
        assert len(contradictions) == 1
        assert contradictions[0].contradiction_type == "direct"

    def test_semantic_contradiction(self):
        """Test semantic contradiction detection."""
        from jarvis_core.analysis.contradiction_detector import ContradictionDetector
        
        detector = ContradictionDetector()
        
        evidence_texts = [
            ("e1", "c1", "Treatment showed increased survival rates"),
            ("e2", "c1", "Treatment showed decreased survival rates"),
        ]
        
        contradictions = detector.detect_semantic_contradictions(evidence_texts)
        
        assert len(contradictions) == 1
        assert contradictions[0].contradiction_type == "semantic"

    def test_detect_all(self):
        """Test full contradiction detection pipeline."""
        from jarvis_core.analysis.contradiction_detector import detect_contradictions
        
        claims = [{"claim_id": "c1", "text": "Test claim"}]
        evidence = [
            {"evidence_id": "e1", "claim_id": "c1", "text": "Higher values observed"},
            {"evidence_id": "e2", "claim_id": "c1", "text": "Lower values observed"},
        ]
        stance_results = [
            {"evidence_id": "e1", "claim_id": "c1", "stance": "supports", "confidence": 0.8},
            {"evidence_id": "e2", "claim_id": "c1", "stance": "contradicts", "confidence": 0.7},
        ]
        
        contradictions, stats = detect_contradictions(claims, evidence, stance_results)
        
        assert "total_contradictions" in stats
        assert "claims_with_contradictions" in stats


class TestPhase2Integration:
    """Integration tests for Phase 2 components."""

    def test_all_modules_import(self):
        """Test all Phase 2 modules can be imported."""
        from jarvis_core.analysis.grade_system import (
            GRADELevel,
            RuleBasedGrader,
            EnsembleGrader,
            grade_evidence_with_grade,
        )
        from jarvis_core.analysis.citation_stance import (
            CitationStance,
            RuleBasedStanceClassifier,
            analyze_citations,
        )
        from jarvis_core.analysis.contradiction_detector import (
            ContradictionDetector,
            detect_contradictions,
        )
        
        assert GRADELevel is not None
        assert CitationStance is not None
        assert ContradictionDetector is not None
