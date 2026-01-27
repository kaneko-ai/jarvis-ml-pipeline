"""
Tabular Metrics Module

accuracy, mse, rmse 等
"""

from __future__ import annotations

import logging
from typing import Dict

import numpy as np

try:
    from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
except ImportError:
    accuracy_score = None
    mean_squared_error = None
    r2_score = None

logger = logging.getLogger(__name__)


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    task: str = "classification",
) -> Dict[str, float]:
    """
    メトリクスを計算.

    Args:
        y_true: 正解
        y_pred: 予測
        task: classification or regression

    Returns:
        メトリクス辞書
    """
    metrics = {}

    if task == "classification":
        metrics["accuracy"] = accuracy_score(y_true, y_pred)
    else:  # regression
        metrics["mse"] = mean_squared_error(y_true, y_pred)
        metrics["rmse"] = np.sqrt(metrics["mse"])
        metrics["r2"] = r2_score(y_true, y_pred)

    logger.info(f"Metrics: {metrics}")
    return metrics
