"""Tests for RP-355+ LLM features.

Core tests for LLM enhancements.
"""
import pytest

pytestmark = pytest.mark.core


class TestMultiModelEnsemble:
    """Tests for RP-355 Multi-Model Ensemble."""

    def test_single_model(self):
        """Should work with single model."""
        from jarvis_core.llm.ensemble import MultiModelEnsemble

        def mock_gen(prompt):
            return f"Response to: {prompt}"

        ensemble = MultiModelEnsemble()
        ensemble.add_model("mock", mock_gen, weight=1.0)

        result = ensemble.generate("test prompt")

        assert result.final_text
        assert result.selected_model == "mock"

    def test_multiple_models(self):
        """Should combine multiple models."""
        from jarvis_core.llm.ensemble import MultiModelEnsemble

        def gen_a(prompt):
            return "Response A"

        def gen_b(prompt):
            return "Response B"

        ensemble = MultiModelEnsemble()
        ensemble.add_model("a", gen_a, weight=1.0)
        ensemble.add_model("b", gen_b, weight=0.5)

        result = ensemble.generate("test")

        assert len(result.model_outputs) == 2
        assert result.final_text in ["Response A", "Response B"]
