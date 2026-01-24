"""
Tabular Preprocessing Module

StandardScaler等の前処理
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
logger = logging.getLogger(__name__)
try:
    from sklearn.preprocessing import StandardScaler
except ImportError:
    StandardScaler = None
    logger.warning("scikit-learn not installed. Some tabular features will be unavailable.")


def create_preprocessor(standardize: bool = True) -> Optional[StandardScaler]:
    """前処理器を作成."""
    if standardize:
        return StandardScaler()
    return None


def fit_transform(
    X_train: pd.DataFrame,
    scaler: Optional[StandardScaler] = None,
) -> Tuple[np.ndarray, Optional[StandardScaler]]:
    """
    訓練データでfit_transform.
    
    Args:
        X_train: 訓練データ
        scaler: StandardScaler（Noneならそのまま返す）
    
    Returns:
        (変換後データ, scaler)
    """
    X = X_train.values.astype(np.float32)

    if scaler is not None:
        X = scaler.fit_transform(X)
        logger.info("StandardScaler fitted and applied")

    return X, scaler


def transform(
    X: pd.DataFrame,
    scaler: Optional[StandardScaler] = None,
) -> np.ndarray:
    """
    scalerで変換（transform only）.
    
    Args:
        X: データ
        scaler: StandardScaler
    
    Returns:
        変換後データ
    """
    X_arr = X.values.astype(np.float32)

    if scaler is not None:
        X_arr = scaler.transform(X_arr)

    return X_arr


def save_scaler(scaler: StandardScaler, output_path: str) -> Path:
    """Scalerを保存."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'wb') as f:
        pickle.dump(scaler, f)

    logger.info(f"Scaler saved: {path}")
    return path


def load_scaler(scaler_path: str) -> StandardScaler:
    """Scalerを読み込み."""
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    return scaler
