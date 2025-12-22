"""Remediation package."""
from .actions import (
    RemediationAction,
    ActionResult,
    SwitchFetchAdapter,
    IncreaseTopK,
    TightenMMR,
    CitationFirstPrompt,
    BudgetRebalance,
    ModelRouterSafeSwitch,
    BUILTIN_ACTIONS,
)
from .catalog import (
    ActionCatalog,
    DuplicateActionError,
    get_catalog,
    get_action,
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
