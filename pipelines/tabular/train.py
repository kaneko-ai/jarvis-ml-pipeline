"""
Tabular Train Module

学習ループ（sklearn/torch共通IF）
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .models.baseline_lr import BaselineLogisticRegression
from .models.baseline_ridge import BaselineRidgeRegression

logger = logging.getLogger(__name__)


def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: Optional[np.ndarray] = None,
    y_val: Optional[np.ndarray] = None,
    task: str = "classification",
    model_type: str = "logistic_regression",
    model_params: Optional[Dict[str, Any]] = None,
) -> Tuple[Any, Dict[str, float]]:
    """
    モデルを学習.

    Args:
        X_train: 訓練特徴量
        y_train: 訓練ラベル
        X_val: 検証特徴量
        y_val: 検証ラベル
        task: classification or regression
        model_type: モデルタイプ
        model_params: モデルパラメータ

    Returns:
        (model, metrics_dict)
    """
    params = model_params or {}

    if task == "classification":
        if model_type == "logistic_regression":
            model = BaselineLogisticRegression(
                max_iter=params.get("max_iter", 2000),
                random_state=params.get("random_state", 0),
            )
        else:
            raise ValueError(f"Unknown classification model: {model_type}")
    else:  # regression
        if model_type == "ridge":
            model = BaselineRidgeRegression(
                alpha=params.get("alpha", 1.0),
                random_state=params.get("random_state", 0),
            )
        else:
            raise ValueError(f"Unknown regression model: {model_type}")

    # 学習
    model.fit(X_train, y_train)

    # メトリクス計算
    metrics = {}
    metrics["train_score"] = model.score(X_train, y_train)

    if X_val is not None and y_val is not None:
        metrics["val_score"] = model.score(X_val, y_val)

    logger.info(f"Training complete: {metrics}")

    return model, metrics
