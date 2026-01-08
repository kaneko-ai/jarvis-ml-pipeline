"""JARVIS Active Learning Module.

Active learning engine for efficient paper screening.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.5
"""

from jarvis_core.active_learning.engine import (
    ActiveLearningEngine,
    ALConfig,
    ALState,
)
from jarvis_core.active_learning.query import (
    DiversitySampling,
    QueryStrategy,
    UncertaintySampling,
)
from jarvis_core.active_learning.stopping import (
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
