"""Tests for truth.enforce module."""

from unittest.mock import MagicMock, patch

from jarvis_core.truth.enforce import (
    enforce_fact_evidence,
    downgrade_to_inference,
    enforce_artifact_truth,
)


class TestEnforceFactEvidence:
    def test_valid_fact_with_evidence(self):
        fact = MagicMock()
        fact.statement = "Valid fact with evidence"
        fact.evidence_refs = [MagicMock()]  # Has evidence
        
        valid, downgraded, flags = enforce_fact_evidence([fact])
        
        assert len(valid) == 1
        assert len(downgraded) == 0
        assert len(flags) == 0

    def test_fact_without_evidence_downgraded(self):
        fact = MagicMock()
        fact.statement = "Fact without evidence"
        fact.evidence_refs = []  # No evidence
        
        valid, downgraded, flags = enforce_fact_evidence([fact])
        
        assert len(valid) == 0
        assert len(downgraded) == 1
        assert "根拠不足により降格" in downgraded[0].statement
        assert len(flags) == 1

    def test_mixed_facts(self):
        fact_with = MagicMock()
        fact_with.statement = "With evidence"
        fact_with.evidence_refs = [MagicMock()]
        
        fact_without = MagicMock()
        fact_without.statement = "Without evidence"
        fact_without.evidence_refs = []
        
        valid, downgraded, flags = enforce_fact_evidence([fact_with, fact_without])
        
        assert len(valid) == 1
        assert len(downgraded) == 1


class TestDowngradeToInference:
    def test_downgrade_basic(self):
        fact = MagicMock()
        fact.statement = "Original fact"
        fact.confidence = 0.8
        
        inference = downgrade_to_inference(fact)
        
        assert "推定" in inference.statement
        assert inference.method == "downgrade_from_fact"
        assert inference.confidence <= 0.4  # max(0.8*0.5, 0.4) = 0.4


class TestEnforceArtifactTruth:
    def test_enforce_artifact(self):
        # Create mock artifact
        artifact = MagicMock()
        artifact.kind = "analysis"
        artifact.facts = []
        artifact.inferences = []
        artifact.recommendations = []
        artifact.metrics = {}
        artifact.confidence = 0.5
        artifact.provenance = MagicMock()
        artifact.raw_data = {}
        
        # Add fact without evidence
        fact = MagicMock()
        fact.statement = "Unverified claim"
        fact.evidence_refs = []
        artifact.facts = [fact]
        
        result = enforce_artifact_truth(artifact)
        
        # Fact should be downgraded
        assert len(result.facts) == 0
        assert len(result.inferences) == 1
        assert "truth_enforcement_flags" in result.raw_data
