"""
Tabular Predict Module

推論
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def predict(model: Any, X: np.ndarray) -> np.ndarray:
    """
    推論を実行.

    Args:
        model: 学習済みモデル
        X: 特徴量

    Returns:
        予測値
    """
    predictions = model.predict(X)
    logger.info(f"Prediction complete: {len(predictions)} samples")
    return predictions
