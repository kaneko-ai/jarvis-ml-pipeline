"""Tests for the Paper Scoring Module.

Per JARVIS_COMPLETION_PLAN_v3 Sprint 19-20
"""

import pytest


class TestScoringWeights:
    """Tests for scoring weights configuration."""

    def test_default_weights(self):
        """Test default scoring weights."""
        from jarvis_core.paper_scoring import ScoringWeights
        
        weights = ScoringWeights()
        
        assert weights.evidence_weight > 0
        assert weights.citation_weight > 0
        assert weights.recency_weight > 0
        assert weights.source_weight > 0
        
        # Weights should sum to approximately 1.0
        total = (
            weights.evidence_weight +
            weights.citation_weight +
            weights.recency_weight +
            weights.source_weight
        )
        assert 0.99 <= total <= 1.01

    def test_custom_weights(self):
        """Test custom scoring weights."""
        from jarvis_core.paper_scoring import ScoringWeights
        
        weights = ScoringWeights(
            evidence_weight=0.4,
            citation_weight=0.3,
            recency_weight=0.2,
            source_weight=0.1,
        )
        
        assert weights.evidence_weight == 0.4
        assert weights.citation_weight == 0.3

    def test_weights_normalization(self):
        """Test weights auto-normalization."""
        from jarvis_core.paper_scoring import ScoringWeights
        
        weights = ScoringWeights(
            evidence_weight=4,
            citation_weight=3,
            recency_weight=2,
            source_weight=1,
            normalize=True,
        )
        
        total = (
            weights.evidence_weight +
            weights.citation_weight +
            weights.recency_weight +
            weights.source_weight
        )
        assert 0.99 <= total <= 1.01


class TestPaperScore:
    """Tests for PaperScore dataclass."""

    def test_paper_score_creation(self):
        """Test PaperScore creation."""
        from jarvis_core.paper_scoring import PaperScore
        
        score = PaperScore(
            paper_id="paper_123",
            overall_score=0.85,
            evidence_score=0.90,
            citation_score=0.80,
            recency_score=0.75,
            source_score=0.95,
        )
        
        assert score.paper_id == "paper_123"
        assert score.overall_score == 0.85

    def test_paper_score_to_dict(self):
        """Test PaperScore serialization."""
        from jarvis_core.paper_scoring import PaperScore
        
        score = PaperScore(
            paper_id="paper_456",
            overall_score=0.72,
            evidence_score=0.80,
            citation_score=0.60,
            recency_score=0.70,
            source_score=0.85,
        )
        
        result = score.to_dict()
        
        assert result["paper_id"] == "paper_456"
        assert result["overall_score"] == 0.72
        assert "evidence_score" in result

    def test_paper_score_comparison(self):
        """Test PaperScore comparison."""
        from jarvis_core.paper_scoring import PaperScore
        
        score_a = PaperScore(paper_id="a", overall_score=0.80)
        score_b = PaperScore(paper_id="b", overall_score=0.90)
        
        assert score_b > score_a
        assert score_a < score_b


class TestPaperScorer:
    """Tests for PaperScorer class."""

    def test_scorer_initialization(self):
        """Test PaperScorer initialization."""
        from jarvis_core.paper_scoring import PaperScorer
        
        scorer = PaperScorer()
        assert scorer is not None

    def test_scorer_with_custom_weights(self):
        """Test PaperScorer with custom weights."""
        from jarvis_core.paper_scoring import PaperScorer, ScoringWeights
        
        weights = ScoringWeights(
            evidence_weight=0.5,
            citation_weight=0.2,
            recency_weight=0.2,
            source_weight=0.1,
        )
        scorer = PaperScorer(weights=weights)
        
        assert scorer.weights.evidence_weight == 0.5

    def test_score_paper_basic(self):
        """Test basic paper scoring."""
        from jarvis_core.paper_scoring import PaperScorer
        from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType
        
        scorer = PaperScorer()
        
        paper = {
            "paper_id": "test_001",
            "title": "A randomized controlled trial",
            "year": 2024,
            "citation_count": 50,
            "source": "pubmed",
        }
        
        evidence_grade = EvidenceGrade(
            level=EvidenceLevel.LEVEL_1B,
            study_type=StudyType.RCT,
            confidence=0.9,
        )
        
        score = scorer.score(paper, evidence_grade=evidence_grade)
        
        assert score.paper_id == "test_001"
        assert 0 <= score.overall_score <= 1
        assert score.evidence_score > 0

    def test_score_paper_high_evidence(self):
        """Test scoring paper with high evidence level."""
        from jarvis_core.paper_scoring import PaperScorer
        from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType
        
        scorer = PaperScorer()
        
        paper = {
            "paper_id": "meta_001",
            "year": 2024,
            "citation_count": 100,
            "source": "cochrane",
        }
        
        evidence_grade = EvidenceGrade(
            level=EvidenceLevel.LEVEL_1A,
            study_type=StudyType.SYSTEMATIC_REVIEW,
            confidence=0.95,
        )
        
        score = scorer.score(paper, evidence_grade=evidence_grade)
        
        # High evidence level should result in high evidence score
        assert score.evidence_score >= 0.9

    def test_score_paper_low_evidence(self):
        """Test scoring paper with low evidence level."""
        from jarvis_core.paper_scoring import PaperScorer
        from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType
        
        scorer = PaperScorer()
        
        paper = {
            "paper_id": "opinion_001",
            "year": 2020,
            "citation_count": 5,
            "source": "preprint",
        }
        
        evidence_grade = EvidenceGrade(
            level=EvidenceLevel.LEVEL_5,
            study_type=StudyType.EXPERT_OPINION,
            confidence=0.6,
        )
        
        score = scorer.score(paper, evidence_grade=evidence_grade)
        
        # Low evidence level should result in lower evidence score
        assert score.evidence_score < 0.5

    def test_recency_scoring(self):
        """Test recency component of scoring."""
        from jarvis_core.paper_scoring import PaperScorer
        
        scorer = PaperScorer()
        
        recent_paper = {"paper_id": "recent", "year": 2025}
        old_paper = {"paper_id": "old", "year": 2010}
        
        recent_score = scorer.score(recent_paper)
        old_score = scorer.score(old_paper)
        
        assert recent_score.recency_score > old_score.recency_score

    def test_citation_scoring(self):
        """Test citation component of scoring."""
        from jarvis_core.paper_scoring import PaperScorer
        
        scorer = PaperScorer()
        
        highly_cited = {"paper_id": "popular", "citation_count": 500}
        low_cited = {"paper_id": "new", "citation_count": 2}
        
        high_score = scorer.score(highly_cited)
        low_score = scorer.score(low_cited)
        
        assert high_score.citation_score > low_score.citation_score

    def test_source_scoring(self):
        """Test source component of scoring."""
        from jarvis_core.paper_scoring import PaperScorer
        
        scorer = PaperScorer()
        
        pubmed_paper = {"paper_id": "pm", "source": "pubmed"}
        preprint_paper = {"paper_id": "pp", "source": "preprint"}
        
        pubmed_score = scorer.score(pubmed_paper)
        preprint_score = scorer.score(preprint_paper)
        
        # Peer-reviewed source should score higher
        assert pubmed_score.source_score >= preprint_score.source_score

    def test_batch_scoring(self):
        """Test batch paper scoring."""
        from jarvis_core.paper_scoring import PaperScorer
        
        scorer = PaperScorer()
        
        papers = [
            {"paper_id": f"paper_{i}", "year": 2020 + i, "citation_count": i * 10}
            for i in range(10)
        ]
        
        scores = scorer.score_batch(papers)
        
        assert len(scores) == 10
        assert all(hasattr(s, "overall_score") for s in scores)


class TestCalculatePaperScoreFunction:
    """Tests for convenience function."""

    def test_calculate_paper_score_basic(self):
        """Test calculate_paper_score function."""
        from jarvis_core.paper_scoring import calculate_paper_score
        
        paper = {
            "paper_id": "func_test",
            "year": 2023,
            "citation_count": 25,
        }
        
        score = calculate_paper_score(paper)
        
        assert score.paper_id == "func_test"
        assert 0 <= score.overall_score <= 1

    def test_calculate_paper_score_with_evidence(self):
        """Test calculate_paper_score with evidence grade."""
        from jarvis_core.paper_scoring import calculate_paper_score
        from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType
        
        paper = {"paper_id": "with_evidence"}
        evidence = EvidenceGrade(
            level=EvidenceLevel.LEVEL_2B,
            study_type=StudyType.COHORT_PROSPECTIVE,
            confidence=0.8,
        )
        
        score = calculate_paper_score(paper, evidence_grade=evidence)
        
        assert score.evidence_score > 0


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.paper_scoring import (
            PaperScore,
            PaperScorer,
            ScoringWeights,
            calculate_paper_score,
        )
        
        assert PaperScore is not None
        assert PaperScorer is not None
        assert ScoringWeights is not None
        assert calculate_paper_score is not None
