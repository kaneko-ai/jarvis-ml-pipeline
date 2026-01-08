"""Remediation package."""
from .actions import (
    BUILTIN_ACTIONS,
    ActionResult,
    BudgetRebalance,
    CitationFirstPrompt,
    IncreaseTopK,
    ModelRouterSafeSwitch,
    RemediationAction,
    SwitchFetchAdapter,
    TightenMMR,
)
from .catalog import (
    ActionCatalog,
    DuplicateActionError,
    get_action,
    get_catalog,
)

__all__ = [
    "RemediationAction",
    "ActionResult",
    "SwitchFetchAdapter",
    "IncreaseTopK",
    "TightenMMR",
    "CitationFirstPrompt",
    "BudgetRebalance",
    "ModelRouterSafeSwitch",
    "BUILTIN_ACTIONS",
    "ActionCatalog",
    "DuplicateActionError",
    "get_catalog",
    "get_action",
]
