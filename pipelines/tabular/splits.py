"""
Tabular Split Module

データ分割（60/20/20固定、seed=0）
"""

from __future__ import annotations

import logging
from typing import Tuple

import numpy as np
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


def split_data(
    X: np.ndarray,
    y: np.ndarray,
    seed: int = 0,
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    データを train/val/test に分割.
    
    デフォルト: 60/20/20（教材準拠）
    
    Args:
        X: 特徴量
        y: ラベル
        seed: 乱数シード（0固定）
        train_ratio: 訓練比率
        val_ratio: 検証比率
        test_ratio: テスト比率
    
    Returns:
        (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "Ratios must sum to 1"

    # 再現性のためseed固定
    np.random.seed(seed)

    # まず train と (val+test) に分割
    val_test_ratio = val_ratio + test_ratio
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y,
        test_size=val_test_ratio,
        random_state=seed,
        stratify=y if is_classification(y) else None,
    )

    # 次に val と test に分割
    val_in_temp = val_ratio / val_test_ratio
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp,
        test_size=1 - val_in_temp,
        random_state=seed,
        stratify=y_temp if is_classification(y_temp) else None,
    )

    logger.info(
        f"Split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}"
    )

    return X_train, X_val, X_test, y_train, y_val, y_test


def is_classification(y: np.ndarray) -> bool:
    """分類タスクかどうか判定."""
    unique = np.unique(y)
    # ユニーク値が少なく、整数なら分類
    if len(unique) <= 20 and np.issubdtype(unique.dtype, np.integer):
        return True
    return False
