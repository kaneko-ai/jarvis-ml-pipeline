"""
Tabular I/O Module

CSV読み込み、スキーマ検証、列整合チェック
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class DataSchema:
    """データスキーマ."""

    train_shape: Tuple[int, int]
    test_shape: Tuple[int, int]
    feature_columns: List[str]
    label_column: str
    dtypes: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "train_shape": list(self.train_shape),
            "test_shape": list(self.test_shape),
            "feature_columns": self.feature_columns,
            "label_column": self.label_column,
            "dtypes": self.dtypes,
        }


def load_train_test(
    train_path: str,
    test_path: str,
    label_col: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, DataSchema]:
    """
    train/testを読み込み、スキーマ検証.

    Args:
        train_path: 訓練データパス
        test_path: テストデータパス
        label_col: ラベル列名

    Returns:
        (X_train, X_test, y_train, schema)

    Raises:
        ValueError: 列不整合、ラベル欠損等
    """
    # 読み込み
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    logger.info(f"Loaded train: {train_df.shape}, test: {test_df.shape}")

    # ラベル列の存在確認
    if label_col not in train_df.columns:
        raise ValueError(
            f"Label column '{label_col}' not found in train. "
            f"Available columns: {list(train_df.columns)}"
        )

    # ラベル列がtestに含まれていないことを確認
    if label_col in test_df.columns:
        logger.warning(f"Label column '{label_col}' found in test. Dropping it.")
        test_df = test_df.drop(columns=[label_col])

    # ラベル抽出
    y_train = train_df[label_col]
    X_train = train_df.drop(columns=[label_col])
    X_test = test_df

    # 列名比較
    train_cols = list(X_train.columns)
    test_cols = list(X_test.columns)

    train_set = set(train_cols)
    test_set = set(test_cols)

    # 列名セットが異なる場合はエラー
    if train_set != test_set:
        missing_in_test = train_set - test_set
        extra_in_test = test_set - train_set

        error_msg = "Column mismatch between train and test.\n"
        if missing_in_test:
            error_msg += f"  Missing in test: {missing_in_test}\n"
        if extra_in_test:
            error_msg += f"  Extra in test: {extra_in_test}\n"
        error_msg += "  Action: Ensure train and test have identical feature columns."

        raise ValueError(error_msg)

    # 列順が異なる場合は警告して揃える
    if train_cols != test_cols:
        logger.warning("Column order differs. Reordering test columns to match train.")

    # 列順を固定（train基準）
    X_test = X_test[train_cols]

    # スキーマ生成
    schema = DataSchema(
        train_shape=train_df.shape,
        test_shape=test_df.shape,
        feature_columns=train_cols,
        label_column=label_col,
        dtypes={col: str(X_train[col].dtype) for col in train_cols},
    )

    logger.info(f"Schema validated: {len(train_cols)} features")

    return X_train, X_test, y_train, schema


def validate_schema(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
) -> bool:
    """
    スキーマ検証.

    Returns:
        True if valid

    Raises:
        ValueError: 検証失敗
    """
    # 列名一致
    if list(X_train.columns) != list(X_test.columns):
        raise ValueError("Feature columns do not match between train and test")

    # 行数チェック
    if len(X_train) != len(y_train):
        raise ValueError(f"X_train rows ({len(X_train)}) != y_train rows ({len(y_train)})")

    # 欠損値チェック（警告のみ）
    train_nulls = X_train.isnull().sum().sum()
    test_nulls = X_test.isnull().sum().sum()
    if train_nulls > 0:
        logger.warning(f"Train has {train_nulls} null values")
    if test_nulls > 0:
        logger.warning(f"Test has {test_nulls} null values")

    return True


def save_schema(schema: DataSchema, output_path: str) -> Path:
    """スキーマをJSONで保存."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema.to_dict(), f, indent=2, ensure_ascii=False)

    logger.info(f"Schema saved to {path}")
    return path
