"""Evaluation package."""
from .goldset_schema import (
    GoldsetEntry,
    GoldsetLabel,
    validate_goldset,
    load_goldset,
    save_goldset,
)
from .metrics_truth import (
    calculate_truth_metrics,
    TruthMetrics,
)
from .regression_runner import (
    run_regression,
    RegressionResult,
)

__all__ = [
    "GoldsetEntry",
    "GoldsetLabel",
    "validate_goldset",
    "load_goldset",
    "save_goldset",
    "calculate_truth_metrics",
    "TruthMetrics",
    "run_regression",
    "RegressionResult",
]
