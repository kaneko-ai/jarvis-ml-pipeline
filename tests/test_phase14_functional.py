"""Phase 14: Function-Level Mock Tests for Maximum Coverage.

These tests execute actual function code paths with proper mocking.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import tempfile
from pathlib import Path
import json


# ============================================================
# Tests for kill_switch.py - All Functions
# ============================================================

class TestKillSwitchFunctional:
    """Comprehensive tests for kill_switch module - all functions."""

    def test_kill_category_enum(self):
        """Test KillCategory enum values."""
        from jarvis_core.kill_switch import KillCategory
        assert KillCategory.KILL_A.value == "structure_broken"
        assert KillCategory.KILL_B.value == "quality_degraded"
        assert KillCategory.KILL_C.value == "reproducibility_lost"
        assert KillCategory.KILL_D.value == "automation_runaway"
        assert KillCategory.KILL_E.value == "operational_risk"

    def test_kill_severity_enum(self):
        """Test KillSeverity enum values."""
        from jarvis_core.kill_switch import KillSeverity
        assert KillSeverity.CRITICAL.value == "critical"
        assert KillSeverity.HIGH.value == "high"
        assert KillSeverity.MEDIUM.value == "medium"
        assert KillSeverity.LOW.value == "low"

    def test_kill_condition_dataclass(self):
        """Test KillCondition dataclass."""
        from jarvis_core.kill_switch import KillCondition, KillCategory, KillSeverity
        cond = KillCondition(
            id="TEST-001",
            category=KillCategory.KILL_A,
            severity=KillSeverity.CRITICAL,
            description="Test condition",
            check_function="test_check",
            action="test_action"
        )
        assert cond.id == "TEST-001"
        assert cond.category == KillCategory.KILL_A

    def test_kill_event_dataclass(self):
        """Test KillEvent dataclass."""
        from jarvis_core.kill_switch import KillEvent, KillCategory, KillSeverity
        event = KillEvent(
            condition_id="TEST-001",
            category=KillCategory.KILL_A,
            severity=KillSeverity.CRITICAL,
            timestamp="2024-01-01T00:00:00Z",
            details={"key": "value"},
            action_taken="test_action"
        )
        assert event.condition_id == "TEST-001"
        assert event.details == {"key": "value"}

    def test_kill_conditions_list(self):
        """Test KILL_CONDITIONS list."""
        from jarvis_core.kill_switch import KILL_CONDITIONS
        assert len(KILL_CONDITIONS) > 0
        assert KILL_CONDITIONS[0].id == "KILL-A-001"

    def test_kill_switch_init(self):
        """Test KillSwitch initialization."""
        from jarvis_core.kill_switch import KillSwitch
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KillSwitch(incidents_file=f"{tmpdir}/incidents.md")
            assert ks.is_killed == False
            assert ks.kill_reason is None
            assert ks.events == []

    def test_kill_switch_check_retry_limit_exceeded(self):
        """Test check_retry_limit when exceeded."""
        from jarvis_core.kill_switch import KillSwitch
        ks = KillSwitch()
        assert ks.check_retry_limit(5, max_retries=3) == True

    def test_kill_switch_check_retry_limit_not_exceeded(self):
        """Test check_retry_limit when not exceeded."""
        from jarvis_core.kill_switch import KillSwitch
        ks = KillSwitch()
        assert ks.check_retry_limit(2, max_retries=3) == False

    def test_kill_switch_check_retry_limit_boundary(self):
        """Test check_retry_limit at boundary."""
        from jarvis_core.kill_switch import KillSwitch
        ks = KillSwitch()
        assert ks.check_retry_limit(3, max_retries=3) == False
        assert ks.check_retry_limit(4, max_retries=3) == True

    def test_kill_switch_check_no_citation_success_true(self):
        """Test check_no_citation_success when true."""
        from jarvis_core.kill_switch import KillSwitch
        ks = KillSwitch()
        result = {"status": "success", "citations": []}
        assert ks.check_no_citation_success(result) == True

    def test_kill_switch_check_no_citation_success_false(self):
        """Test check_no_citation_success when false."""
        from jarvis_core.kill_switch import KillSwitch
        ks = KillSwitch()
        result = {"status": "success", "citations": ["citation1"]}
        assert ks.check_no_citation_success(result) == False

    def test_kill_switch_check_no_citation_not_success(self):
        """Test check_no_citation_success when not success."""
        from jarvis_core.kill_switch import KillSwitch
        ks = KillSwitch()
        result = {"status": "failed", "citations": []}
        assert ks.check_no_citation_success(result) == False

    def test_kill_switch_check_gate_fail_success_true(self):
        """Test check_gate_fail_success when true."""
        from jarvis_core.kill_switch import KillSwitch
        ks = KillSwitch()
        result = {"status": "success"}
        eval_summary = {"gate_passed": False}
        assert ks.check_gate_fail_success(result, eval_summary) == True

    def test_kill_switch_check_gate_fail_success_false(self):
        """Test check_gate_fail_success when false."""
        from jarvis_core.kill_switch import KillSwitch
        ks = KillSwitch()
        result = {"status": "success"}
        eval_summary = {"gate_passed": True}
        assert ks.check_gate_fail_success(result, eval_summary) == False

    def test_kill_switch_get_condition_by_id_found(self):
        """Test get_condition_by_id when found."""
        from jarvis_core.kill_switch import KillSwitch
        ks = KillSwitch()
        cond = ks.get_condition_by_id("KILL-A-001")
        assert cond is not None
        assert cond.id == "KILL-A-001"

    def test_kill_switch_get_condition_by_id_not_found(self):
        """Test get_condition_by_id when not found."""
        from jarvis_core.kill_switch import KillSwitch
        ks = KillSwitch()
        cond = ks.get_condition_by_id("NONEXISTENT")
        assert cond is None

    def test_kill_switch_trigger_kill(self):
        """Test trigger_kill method."""
        from jarvis_core.kill_switch import KillSwitch, KillCondition, KillCategory, KillSeverity
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KillSwitch(incidents_file=f"{tmpdir}/incidents.md")
            cond = KillCondition(
                id="TEST-001",
                category=KillCategory.KILL_A,
                severity=KillSeverity.CRITICAL,
                description="Test condition",
                check_function="test_check",
                action="test_action"
            )
            event = ks.trigger_kill(cond, {"test": "details"})
            assert event.condition_id == "TEST-001"
            assert ks.is_killed == True
            assert "TEST-001" in ks.kill_reason

    def test_kill_switch_trigger_kill_non_critical(self):
        """Test trigger_kill with non-critical severity."""
        from jarvis_core.kill_switch import KillSwitch, KillCondition, KillCategory, KillSeverity
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KillSwitch(incidents_file=f"{tmpdir}/incidents.md")
            cond = KillCondition(
                id="TEST-002",
                category=KillCategory.KILL_B,
                severity=KillSeverity.HIGH,  # Not CRITICAL
                description="Test condition",
                check_function="test_check",
                action="test_action"
            )
            event = ks.trigger_kill(cond, {"test": "details"})
            assert event.condition_id == "TEST-002"
            assert ks.is_killed == False  # Should not be killed

    def test_recommend_kill_switch_empty_vectors(self):
        """Test recommend_kill_switch with empty vectors."""
        from jarvis_core.kill_switch import recommend_kill_switch
        result = recommend_kill_switch("test_theme", [], months_invested=12)
        assert result["recommendation"] == "stop"
        assert result["stop_score"] == 1.0
        assert result["theme"] == "test_theme"

    def test_recommend_kill_switch_continue(self):
        """Test recommend_kill_switch with high-value vectors."""
        from jarvis_core.kill_switch import recommend_kill_switch
        mock_vector = MagicMock()
        mock_vector.temporal.novelty = 0.8
        mock_vector.impact.future_potential = 0.7
        result = recommend_kill_switch("test_theme", [mock_vector], months_invested=6)
        assert result["recommendation"] == "continue"
        assert result["continue_score"] >= 0.6

    def test_recommend_kill_switch_pivot(self):
        """Test recommend_kill_switch with moderate vectors."""
        from jarvis_core.kill_switch import recommend_kill_switch
        mock_vector = MagicMock()
        mock_vector.temporal.novelty = 0.4
        mock_vector.impact.future_potential = 0.4
        result = recommend_kill_switch("test_theme", [mock_vector])
        assert result["recommendation"] == "pivot"

    def test_recommend_kill_switch_stop(self):
        """Test recommend_kill_switch with low-value vectors."""
        from jarvis_core.kill_switch import recommend_kill_switch
        mock_vector = MagicMock()
        mock_vector.temporal.novelty = 0.1
        mock_vector.impact.future_potential = 0.1
        result = recommend_kill_switch("test_theme", [mock_vector])
        assert result["recommendation"] == "stop"

    def test_assess_field_evolution_empty(self):
        """Test assess_field_evolution with empty vectors."""
        from jarvis_core.kill_switch import assess_field_evolution
        result = assess_field_evolution([], "test_field")
        assert result["field"] == "test_field"
        assert result["evolution_index"] == 0.0
        assert result["trend"] == "stagnant"

    def test_assess_field_evolution_with_recent_papers(self):
        """Test assess_field_evolution with recent papers."""
        from jarvis_core.kill_switch import assess_field_evolution
        vectors = []
        for year in [2020, 2021, 2022, 2023]:
            mock = MagicMock()
            mock.metadata.year = year
            vectors.append(mock)
        result = assess_field_evolution(vectors, "test_field")
        assert result["trend"] == "rapidly_evolving"

    def test_assess_field_evolution_with_old_papers(self):
        """Test assess_field_evolution with old papers."""
        from jarvis_core.kill_switch import assess_field_evolution
        vectors = []
        for year in [2010, 2012, 2015, 2018]:
            mock = MagicMock()
            mock.metadata.year = year
            vectors.append(mock)
        result = assess_field_evolution(vectors, "test_field")
        assert result["trend"] in ["mature", "evolving"]


# ============================================================
# Tests for education.py - All Functions
# ============================================================

class TestEducationFunctional:
    """Comprehensive tests for education module - all functions."""

    def test_translate_for_level_highschool(self):
        """Test translate_for_level for highschool."""
        from jarvis_core.education import translate_for_level
        mock_paper = MagicMock()
        mock_paper.concept.top_concepts.return_value = [("concept1", 0.9), ("concept2", 0.8)]
        mock_paper.biological_axis.immune_activation = 0.5
        mock_paper.biological_axis.tumor_context = 0.4
        
        result = translate_for_level(mock_paper, "highschool")
        assert "高校生" in result
        assert "concept1" in result

    def test_translate_for_level_highschool_immune_negative(self):
        """Test highschool translation with negative immune activation."""
        from jarvis_core.education import translate_for_level
        mock_paper = MagicMock()
        mock_paper.concept.top_concepts.return_value = [("concept1", 0.9)]
        mock_paper.biological_axis.immune_activation = -0.5
        mock_paper.biological_axis.tumor_context = 0.2
        
        result = translate_for_level(mock_paper, "highschool")
        assert "抑える" in result

    def test_translate_for_level_highschool_high_tumor(self):
        """Test highschool translation with high tumor context."""
        from jarvis_core.education import translate_for_level
        mock_paper = MagicMock()
        mock_paper.concept.top_concepts.return_value = []
        mock_paper.biological_axis.immune_activation = 0.5
        mock_paper.biological_axis.tumor_context = 0.5
        
        result = translate_for_level(mock_paper, "highschool")
        assert "がん" in result

    def test_translate_for_level_undergrad(self):
        """Test translate_for_level for undergrad."""
        from jarvis_core.education import translate_for_level
        mock_paper = MagicMock()
        mock_paper.concept.top_concepts.return_value = [("immunotherapy", 0.9)]
        mock_paper.biological_axis.immune_activation = 0.5
        mock_paper.biological_axis.tumor_context = 0.4
        mock_paper.method.methods = {"flow_cytometry": 0.8, "western_blot": 0.6}
        
        result = translate_for_level(mock_paper, "undergrad")
        assert "学部生" in result
        assert "immunotherapy" in result

    def test_translate_for_level_undergrad_high_immune(self):
        """Test undergrad with high immune activation."""
        from jarvis_core.education import translate_for_level
        mock_paper = MagicMock()
        mock_paper.concept.top_concepts.return_value = []
        mock_paper.biological_axis.immune_activation = 0.5
        mock_paper.biological_axis.tumor_context = 0.4
        mock_paper.method.methods = {}
        
        result = translate_for_level(mock_paper, "undergrad")
        assert "活性化" in result

    def test_translate_for_level_undergrad_low_immune(self):
        """Test undergrad with low immune activation."""
        from jarvis_core.education import translate_for_level
        mock_paper = MagicMock()
        mock_paper.concept.top_concepts.return_value = []
        mock_paper.biological_axis.immune_activation = -0.5
        mock_paper.biological_axis.tumor_context = 0.4
        mock_paper.method.methods = {}
        
        result = translate_for_level(mock_paper, "undergrad")
        assert "抑制" in result

    def test_translate_for_level_grad(self):
        """Test translate_for_level for grad."""
        from jarvis_core.education import translate_for_level
        mock_paper = MagicMock()
        mock_paper.concept.top_concepts.return_value = [("concept1", 0.9), ("concept2", 0.8)]
        mock_paper.source_locator = "test_source"
        mock_paper.biological_axis.immune_activation = 0.5
        mock_paper.biological_axis.metabolism_signal = 0.3
        mock_paper.biological_axis.tumor_context = 0.4
        mock_paper.temporal.novelty = 0.7
        mock_paper.temporal.paradigm_shift = 0.5
        
        result = translate_for_level(mock_paper, "grad")
        assert "大学院生" in result
        assert "test_source" in result


# ============================================================
# Tests for rehearsal.py - All Functions
# ============================================================

class TestRehearsalFunctional:
    """Comprehensive tests for rehearsal module - all functions."""

    def test_generate_rehearsal_empty(self):
        """Test generate_rehearsal with empty vectors."""
        from jarvis_core.rehearsal import generate_rehearsal
        result = generate_rehearsal([])
        assert result["questions"] == []
        assert result["tough_questions"] == []
        assert result["model_answers"] == []

    def test_generate_rehearsal_with_vectors(self):
        """Test generate_rehearsal with vectors."""
        from jarvis_core.rehearsal import generate_rehearsal
        mock_vector = MagicMock()
        mock_vector.concept.concepts = {"concept1": 0.9, "concept2": 0.8}
        mock_vector.method.methods = {"method1": 0.7}
        mock_vector.metadata.year = 2023
        mock_vector.temporal.novelty = 0.8
        
        result = generate_rehearsal([mock_vector])
        assert len(result["questions"]) > 0
        assert len(result["tough_questions"]) > 0
        assert len(result["model_answers"]) > 0
        assert result["total_papers_reviewed"] == 1

    def test_generate_rehearsal_low_novelty(self):
        """Test generate_rehearsal with low novelty."""
        from jarvis_core.rehearsal import generate_rehearsal
        mock_vector = MagicMock()
        mock_vector.concept.concepts = {}
        mock_vector.method.methods = {}
        mock_vector.metadata.year = None
        mock_vector.temporal.novelty = 0.3
        
        result = generate_rehearsal([mock_vector])
        # Should have additional tough question about low novelty
        assert any("新規性" in q for q in result["tough_questions"])

    def test_generate_rehearsal_multiple_vectors(self):
        """Test generate_rehearsal with multiple vectors."""
        from jarvis_core.rehearsal import generate_rehearsal
        vectors = []
        for i in range(3):
            mock = MagicMock()
            mock.concept.concepts = {f"concept_{i}": 0.9}
            mock.method.methods = {f"method_{i}": 0.8}
            mock.metadata.year = 2020 + i
            mock.temporal.novelty = 0.6
            vectors.append(mock)
        
        result = generate_rehearsal(vectors)
        assert result["total_papers_reviewed"] == 3
        assert len(result["concepts_covered"]) == 3
