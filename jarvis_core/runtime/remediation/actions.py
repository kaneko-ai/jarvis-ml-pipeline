from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Result of applying a remediation action."""

    success: bool
    config_changes: dict[str, Any]
    message: str


class RemediationAction(ABC):
    """Base class for remediation actions.

    All actions must be:
    - Deterministic (same input → same output)
    - Minimal side effects
    - Safe (no PII/secrets in output)
    """

    action_id: str
    description: str

    @abstractmethod
    def apply(self, config: dict[str, Any], state: dict[str, Any]) -> ActionResult:
        """Apply the remediation action.

        Args:
            config: Current run configuration.
            state: Current run state (history, metrics, etc.).

        Returns:
            ActionResult with changes to apply.
        """
        pass

    def can_apply(self, config: dict[str, Any], state: dict[str, Any]) -> bool:
        """Check if this action can be applied."""
        return True


class SwitchFetchAdapter(RemediationAction):
    """RP-193: Switch to next fetch adapter in chain."""

    action_id = "SWITCH_FETCH_ADAPTER"
    description = "Switch to next fetch adapter (Local→PMC→Unpaywall→HTML)"

    ADAPTER_ORDER = ["local", "pmc", "unpaywall", "html_fallback"]

    def apply(self, config: dict[str, Any], state: dict[str, Any]) -> ActionResult:
        current = config.get("fetch_adapter", "local")
        try:
            idx = self.ADAPTER_ORDER.index(current)
            if idx < len(self.ADAPTER_ORDER) - 1:
                next_adapter = self.ADAPTER_ORDER[idx + 1]
                return ActionResult(
                    success=True,
                    config_changes={"fetch_adapter": next_adapter},
                    message=f"Switched adapter: {current} → {next_adapter}",
                )
        except ValueError as e:
            logger.debug(f"Adapter {current} not found in order: {e}")

        return ActionResult(
            success=False,
            config_changes={},
            message="No more adapters available",
        )


class IncreaseTopK(RemediationAction):
    """RP-194/197: Increase retrieval top_k."""

    action_id = "INCREASE_TOP_K"
    description = "Increase retrieval top_k to get more candidates"

    MAX_TOP_K = 50

    def apply(self, config: dict[str, Any], state: dict[str, Any]) -> ActionResult:
        current_k = config.get("top_k", 10)
        new_k = min(current_k + 5, self.MAX_TOP_K)

        if new_k == current_k:
            return ActionResult(
                success=False,
                config_changes={},
                message=f"top_k already at maximum ({self.MAX_TOP_K})",
            )

        return ActionResult(
            success=True,
            config_changes={"top_k": new_k},
            message=f"Increased top_k: {current_k} → {new_k}",
        )


class TightenMMR(RemediationAction):
    """RP-195: Tighten MMR to reduce noise."""

    action_id = "TIGHTEN_MMR"
    description = "Tighten MMR lambda to reduce redundant chunks"

    def apply(self, config: dict[str, Any], state: dict[str, Any]) -> ActionResult:
        current_lambda = config.get("mmr_lambda", 0.5)
        new_lambda = min(current_lambda + 0.1, 0.9)

        if new_lambda == current_lambda:
            return ActionResult(
                success=False,
                config_changes={},
                message="mmr_lambda already at maximum",
            )

        return ActionResult(
            success=True,
            config_changes={"mmr_lambda": new_lambda},
            message=f"Tightened MMR: {current_lambda} → {new_lambda}",
        )


class CitationFirstPrompt(RemediationAction):
    """RP-194: Use citation-first prompt strategy."""

    action_id = "CITATION_FIRST_PROMPT"
    description = "Switch to citation-first generation prompt"

    def apply(self, config: dict[str, Any], state: dict[str, Any]) -> ActionResult:
        if config.get("prompt_strategy") == "citation_first":
            return ActionResult(
                success=False,
                config_changes={},
                message="Already using citation_first strategy",
            )

        return ActionResult(
            success=True,
            config_changes={"prompt_strategy": "citation_first"},
            message="Switched to citation_first prompt strategy",
        )


class BudgetRebalance(RemediationAction):
    """RP-196: Rebalance budget allocation."""

    action_id = "BUDGET_REBALANCE"
    description = "Rebalance budget: prioritize retrieval, shorten generation"

    def apply(self, config: dict[str, Any], state: dict[str, Any]) -> ActionResult:
        current_max_tokens = config.get("max_generation_tokens", 2000)
        new_max_tokens = max(500, current_max_tokens // 2)

        return ActionResult(
            success=True,
            config_changes={
                "max_generation_tokens": new_max_tokens,
                "budget_priority": "retrieval",
            },
            message=f"Rebalanced budget: gen tokens {current_max_tokens} → {new_max_tokens}",
        )


class ModelRouterSafeSwitch(RemediationAction):
    """RP-198: Switch to safer/lighter model."""

    action_id = "MODEL_ROUTER_SAFE_SWITCH"
    description = "Switch to fallback model (lighter or rule-based)"

    def apply(self, config: dict[str, Any], state: dict[str, Any]) -> ActionResult:
        current = config.get("model_provider", "gemini")

        fallback_order = {
            "gemini": "ollama",
            "openai": "gemini",
            "ollama": "rule",
        }

        new_provider = fallback_order.get(current, "rule")

        return ActionResult(
            success=True,
            config_changes={"model_provider": new_provider},
            message=f"Model switch: {current} → {new_provider}",
        )


# All built-in actions
BUILTIN_ACTIONS = [
    SwitchFetchAdapter(),
    IncreaseTopK(),
    TightenMMR(),
    CitationFirstPrompt(),
    BudgetRebalance(),
    ModelRouterSafeSwitch(),
]