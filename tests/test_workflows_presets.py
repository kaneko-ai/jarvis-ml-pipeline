"""Tests for workflow presets module."""

from jarvis_core.workflows.presets import (
    WorkflowPreset,
    PRESETS,
    get_preset,
    list_presets,
    apply_preset,
)


class TestWorkflowPreset:
    def test_preset_init(self):
        preset = WorkflowPreset(
            name="test",
            description="desc",
            workflow="flow",
            max_inputs=5,
            review_mode=True,
            depth="deep",
        )
        assert preset.name == "test"
        assert preset.depth == "deep"

    def test_to_dict(self):
        preset = WorkflowPreset(name="test", description="desc", workflow="flow")
        data = preset.to_dict()
        assert data["name"] == "test"
        assert data["workflow"] == "flow"
        assert data["max_inputs"] == 1  # Default


class TestPresetFunctions:
    def test_get_preset_valid(self):
        preset = get_preset("quick_plan")
        assert preset is not None
        assert preset.name == "quick_plan"

    def test_get_preset_invalid(self):
        preset = get_preset("nonexistent")
        assert preset is None

    def test_list_presets(self):
        presets = list_presets()
        assert len(presets) > 0
        assert "quick_plan" in presets
        assert "deep_plan" in presets

    def test_apply_preset_valid(self):
        config = apply_preset("quick_plan")
        assert config["name"] == "quick_plan"
        assert "depth" in config

    def test_apply_preset_invalid(self):
        config = apply_preset("nonexistent")
        assert config == {}


class TestPresetIntegrity:
    def test_all_presets_valid(self):
        for name, preset in PRESETS.items():
            assert name == preset.name
            assert preset.description
            assert preset.workflow
            assert preset.depth in ["quick", "standard", "deep"]