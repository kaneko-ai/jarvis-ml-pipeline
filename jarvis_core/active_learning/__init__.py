"""JARVIS Active Learning Module.

Active learning engine for efficient paper screening.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.5
"""

from .engine import (
    ActiveLearningEngine,
    ALConfig,
    ALState,
)
from .query import (
    DiversitySampling,
    QueryStrategy,
    UncertaintySampling,
)
from .stopping import (
    BudgetStoppingCriterion,
    RecallStoppingCriterion,
    StoppingCriterion,
)

__all__ = [
    "ActiveLearningEngine",
    "ALConfig",
    "ALState",
    "QueryStrategy",
    "UncertaintySampling",
    "DiversitySampling",
    "StoppingCriterion",
    "RecallStoppingCriterion",
    "BudgetStoppingCriterion",
]