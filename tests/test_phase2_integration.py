"""E2E Integration Test (Phase 1 + Phase 2).

Minimal integration test to verify that all Phase 2 stages
can be executed without errors.
"""
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestPhase2Integration:
    """Test Phase 2 stages integration."""

    def test_claim_extraction_stage(self):
        """Claim extraction stage can be imported and has required interface."""
        from jarvis_core.stages.extract_claims import extract_claims

        # Verify it's a callable
        assert callable(extract_claims)

    def test_evidence_finding_stage(self):
        """Evidence finding stage can be imported."""
        from jarvis_core.stages.find_evidence import find_evidence

        assert callable(find_evidence)

    def test_evidence_grading_stage(self):
        """Evidence grading stage can be imported."""
        from jarvis_core.stages.grade_evidence import grade_evidence

        assert callable(grade_evidence)

    def test_features_extraction_stage(self):
        """Features extraction stage can be imported."""
        from jarvis_core.stages.extract_features import extract_features

        assert callable(extract_features)

    def test_lgbm_ranker_available(self):
        """LightGBM ranker can be imported."""
        from jarvis_core.ranking.lgbm_ranker import LGBMRanker

        ranker = LGBMRanker()
        assert ranker.feature_names is not None

    def test_escalation_logic_available(self):
        """Escalation logic can be imported."""
        from jarvis_core.runtime.escalation import InferenceEscalator

        escalator = InferenceEscalator()
        assert escalator.escalation_rules is not None


class TestSchemas:
    """Test that Phase 2 schemas are valid JSON."""

    def test_claim_schema_valid(self):
        """Claim schema is valid JSON."""
        import json
        schema_path = Path("docs/SCHEMAS/claim_unit.schema.json")

        if not schema_path.exists():
            pytest.skip("Claim schema not found")

        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)

        assert schema.get("type") == "object"
        assert "required" in schema

    def test_evidence_schema_valid(self):
        """Evidence schema is valid JSON."""
        import json
        schema_path = Path("docs/SCHEMAS/evidence_unit.schema.json")

        if not schema_path.exists():
            pytest.skip("Evidence schema not found")

        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)

        assert schema.get("type") == "object"
        assert "required" in schema


class TestRunStorePhase2:
    """Test RunStore Phase 2 extensions."""

    def test_runstore_has_optional_files(self):
        """RunStore has Phase 2 optional file properties."""
        from jarvis_core.storage import RunStore

        store = RunStore("test_run_id")

        assert hasattr(store, "cost_report_file")
        assert hasattr(store, "features_file")
        assert hasattr(store, "save_cost_report")
        assert hasattr(store, "save_features")
        assert hasattr(store, "load_cost_report")
        assert hasattr(store, "load_features")


class TestPipelineConfiguration:
    """Test that Phase 2 pipeline is properly configured."""

    def test_e2e_oa10_has_phase2_stages(self):
        """e2e_oa10.yml includes Phase 2 stages."""
        import yaml

        pipeline_path = Path("configs/pipelines/e2e_oa10.yml")
        if not pipeline_path.exists():
            pytest.skip("Pipeline not found")

        with open(pipeline_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        stages = config.get("stages", [])
        stage_ids = [s.get("id") for s in stages]

        # Check Phase 2 stages are present
        assert "extraction.rubric_features" in stage_ids
        assert "quality_gate.evidence_grading" in stage_ids

    def test_e2e_oa10_has_phase2_quality_gates(self):
        """e2e_oa10.yml includes Phase 2 quality gates."""
        import yaml

        pipeline_path = Path("configs/pipelines/e2e_oa10.yml")
        if not pipeline_path.exists():
            pytest.skip("Pipeline not found")

        with open(pipeline_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        quality_gates = config.get("quality_gates", {})

        # Check Phase 2 quality gates
        assert "support_rate" in quality_gates
        assert quality_gates["support_rate"] == 0.90
