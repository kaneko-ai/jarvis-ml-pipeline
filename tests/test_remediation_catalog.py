"""Tests for Remediation Catalog.

Per RP-185.
"""
import pytest

pytestmark = pytest.mark.core


class TestRemediationCatalog:
    """Tests for action catalog."""

    def test_builtin_actions_registered(self):
        """Built-in actions should be registered."""
        from jarvis_core.runtime.remediation import get_catalog

        catalog = get_catalog()

        expected = [
            "SWITCH_FETCH_ADAPTER",
            "INCREASE_TOP_K",
            "TIGHTEN_MMR",
            "CITATION_FIRST_PROMPT",
            "BUDGET_REBALANCE",
            "MODEL_ROUTER_SAFE_SWITCH",
        ]

        for action_id in expected:
            assert catalog.has(action_id), f"Missing: {action_id}"

    def test_get_action(self):
        """get_action should return action instance."""
        from jarvis_core.runtime.remediation import get_action

        action = get_action("INCREASE_TOP_K")
        assert action is not None
        assert action.action_id == "INCREASE_TOP_K"

    def test_duplicate_action_error(self):
        """Registering duplicate ID should raise error."""
        from jarvis_core.runtime.remediation import (
            ActionCatalog, DuplicateActionError, IncreaseTopK
        )

        catalog = ActionCatalog()
        # First registration done in __init__

        # Try to register again
        with pytest.raises(DuplicateActionError):
            catalog.register(IncreaseTopK())

    def test_action_apply_deterministic(self):
        """Actions should be deterministic."""
        from jarvis_core.runtime.remediation import get_action

        action = get_action("INCREASE_TOP_K")

        config = {"top_k": 10}
        state = {}

        result1 = action.apply(config.copy(), state)
        result2 = action.apply(config.copy(), state)

        # Same input → same output
        assert result1.config_changes == result2.config_changes

    def test_switch_fetch_adapter_order(self):
        """SwitchFetchAdapter should follow defined order."""
        from jarvis_core.runtime.remediation import get_action

        action = get_action("SWITCH_FETCH_ADAPTER")

        # Start with local
        config = {"fetch_adapter": "local"}
        result = action.apply(config, {})
        assert result.config_changes["fetch_adapter"] == "pmc"

        # From pmc
        config = {"fetch_adapter": "pmc"}
        result = action.apply(config, {})
        assert result.config_changes["fetch_adapter"] == "unpaywall"
