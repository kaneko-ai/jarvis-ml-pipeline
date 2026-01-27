"""
Tabular Models - Baseline Ridge Regression

回帰用: Ridge(alpha=1.0)
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path

import numpy as np

try:
    from sklearn.linear_model import Ridge
except ImportError:
    pass

logger = logging.getLogger(__name__)


class BaselineRidgeRegression:
    """ベースライン: Ridge回帰."""

    def __init__(self, alpha: float = 1.0, random_state: int = 0):
        """初期化."""
        self.model = Ridge(alpha=alpha, random_state=random_state)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaselineRidgeRegression":
        """学習."""
        self.model.fit(X, y)
        logger.info(f"Ridge fitted: {X.shape}")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """予測."""
        return self.model.predict(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """R2スコア."""
        return self.model.score(X, y)

    def save(self, path: str) -> Path:
        """保存."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            pickle.dump(self.model, f)
        logger.info(f"Model saved: {p}")
        return p

    @classmethod
    def load(cls, path: str) -> "BaselineRidgeRegression":
        """読み込み."""
        instance = cls()
        with open(path, "rb") as f:
            instance.model = pickle.load(f)
        return instance
