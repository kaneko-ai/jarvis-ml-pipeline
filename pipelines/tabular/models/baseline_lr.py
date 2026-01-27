"""
Tabular Models - Baseline Logistic Regression

分類用: LogisticRegression(max_iter=2000)
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path

import numpy as np

try:
    from sklearn.linear_model import LogisticRegression
except ImportError:
    pass

logger = logging.getLogger(__name__)


class BaselineLogisticRegression:
    """ベースライン: ロジスティック回帰."""

    def __init__(self, max_iter: int = 2000, random_state: int = 0):
        """初期化."""
        self.model = LogisticRegression(
            max_iter=max_iter,
            random_state=random_state,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaselineLogisticRegression":
        """学習."""
        self.model.fit(X, y)
        logger.info(f"LogisticRegression fitted: {X.shape}")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """予測."""
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """確率予測."""
        return self.model.predict_proba(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """精度."""
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
    def load(cls, path: str) -> "BaselineLogisticRegression":
        """読み込み."""
        instance = cls()
        with open(path, "rb") as f:
            instance.model = pickle.load(f)
        return instance
