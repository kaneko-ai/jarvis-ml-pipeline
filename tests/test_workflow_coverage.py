"""Tests for workflow module - Coverage improvement (FIXED)."""


class TestStepStatus:
    """Tests for StepStatus enum."""

    def test_step_status_values(self):
        """Test StepStatus enum values."""
        from jarvis_core.workflow.runner import StepStatus

        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.RUNNING.value == "running"
        assert StepStatus.COMPLETED.value == "completed"
        assert StepStatus.FAILED.value == "failed"


class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_step_result_creation(self):
        """Test StepResult creation."""
        from jarvis_core.workflow.runner import StepResult, StepStatus

        result = StepResult(
            step_id="step1",
            status=StepStatus.COMPLETED,
            output={"key": "value"},
        )

        assert result.step_id == "step1"
        assert result.status == StepStatus.COMPLETED
        assert result.cost == 0.0


class TestWorkflowState:
    """Tests for WorkflowState dataclass."""

    def test_workflow_state_creation(self):
        """Test WorkflowState creation."""
        from jarvis_core.workflow.runner import WorkflowState
        from jarvis_core.workflow.spec import Mode

        state = WorkflowState(
            run_id="run-123",
            workflow_id="workflow-456",
            mode=Mode.STEP,
        )

        assert state.run_id == "run-123"
        assert state.workflow_id == "workflow-456"
        assert state.current_step_index == 0

    def test_to_dict(self):
        """Test WorkflowState to_dict."""
        from jarvis_core.workflow.runner import WorkflowState
        from jarvis_core.workflow.spec import Mode

        state = WorkflowState(
            run_id="run-123",
            workflow_id="workflow-456",
            mode=Mode.STEP,
        )

        result = state.to_dict()
        assert result["run_id"] == "run-123"


class TestContextPackager:
    """Tests for context packager module."""

    def test_context_packager_creation(self):
        """Test ContextPackager creation."""
        from jarvis_core.workflow.context_packager import ContextPackager

        packager = ContextPackager()
        assert packager is not None


class TestWorkflowSpec:
    """Tests for workflow spec module."""

    def test_mode_enum(self):
        """Test Mode enum."""
        from jarvis_core.workflow.spec import Mode

        assert Mode.STEP.value == "step"
        assert Mode.HITL.value == "hitl"

    def test_step_spec_creation(self):
        """Test StepSpec creation."""
        from jarvis_core.workflow.spec import StepSpec

        step = StepSpec(
            step_id="step1",
            action="search",
        )

        assert step.step_id == "step1"
        assert step.action == "search"

    def test_workflow_spec_creation(self):
        """Test WorkflowSpec creation."""
        from jarvis_core.workflow.spec import WorkflowSpec, StepSpec, Mode

        spec = WorkflowSpec(
            workflow_id="workflow1",
            mode=Mode.STEP,
            objective="Test objective",
            steps=[
                StepSpec(step_id="step1", action="search"),
            ],
        )

        assert spec.workflow_id == "workflow1"
        assert len(spec.steps) == 1


class TestModuleImports:
    """Test module imports."""

    def test_workflow_imports(self):
        """Test workflow module imports."""
        from jarvis_core.workflow import (
            runner,
            context_packager,
            spec,
        )

        assert runner is not None
        assert context_packager is not None
        assert spec is not None
