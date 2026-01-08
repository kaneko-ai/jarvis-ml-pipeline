"""
Tabular Submission Module

提出CSV生成と検証
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def make_submission(
    predictions: Union[np.ndarray, List],
    output_path: str,
    target_col: str,
    label_offset: int = 0,
) -> Path:
    """
    提出CSV生成.
    
    Args:
        predictions: 予測値
        output_path: 出力パス
        target_col: 列名（例：class, y）
        label_offset: ラベルオフセット（0始まり→1始まりなら1）
    
    Returns:
        出力ファイルパス
    """
    pred_array = np.array(predictions)

    # オフセット適用
    if label_offset != 0:
        pred_array = pred_array + label_offset
        logger.info(f"Applied label offset: {label_offset}")

    # DataFrame作成
    submission_df = pd.DataFrame({target_col: pred_array})

    # CSV出力（index=False, 改行=\n）
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    submission_df.to_csv(path, index=False, lineterminator='\n')

    logger.info(f"Submission saved: {path} ({len(submission_df)} rows)")

    # 検証
    validate_submission(path, target_col, expected_rows=len(pred_array))

    return path


def validate_submission(
    submission_path: str,
    target_col: str,
    expected_rows: Optional[int] = None,
    expected_classes: Optional[List[int]] = None,
) -> bool:
    """
    提出CSV検証.
    
    Args:
        submission_path: 提出ファイルパス
        target_col: 期待する列名
        expected_rows: 期待する行数
        expected_classes: 期待するクラス値（分類の場合）
    
    Returns:
        True if valid
    
    Raises:
        ValueError: 検証失敗
    """
    path = Path(submission_path)

    if not path.exists():
        raise ValueError(f"Submission file not found: {path}")

    # 再読み込み
    df = pd.read_csv(path)

    # 列名チェック
    if list(df.columns) != [target_col]:
        raise ValueError(
            f"Column name mismatch. Expected: ['{target_col}'], "
            f"Got: {list(df.columns)}"
        )

    # 行数チェック
    if expected_rows is not None and len(df) != expected_rows:
        raise ValueError(
            f"Row count mismatch. Expected: {expected_rows}, "
            f"Got: {len(df)}"
        )

    # クラス値チェック（分類）
    if expected_classes is not None:
        unique_values = set(df[target_col].unique())
        expected_set = set(expected_classes)
        if not unique_values.issubset(expected_set):
            raise ValueError(
                f"Unexpected class values. Expected: {expected_set}, "
                f"Got: {unique_values}"
            )

    # 改行チェック
    with open(path, 'rb') as f:
        content = f.read()
        if b'\r\n' in content:
            logger.warning("Windows line endings detected. Should use \\n only.")

    logger.info(f"Submission validated: {path}")
    return True
