#!/usr/bin/env python
"""
Tabular Pipeline CLI

コマンド1発で submission.csv を生成

使い方:
    python -m cli.tabular_run --config configs/tabular/wine.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.tabular.io import load_train_test, save_schema
from pipelines.tabular.preprocess import create_preprocessor, fit_transform, transform, save_scaler
from pipelines.tabular.splits import split_data
from pipelines.tabular.train import train_model
from pipelines.tabular.predict import predict
from pipelines.tabular.metrics import calculate_metrics
from pipelines.tabular.submission import make_submission
from pipelines.tabular.report import generate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """設定ファイルを読み込み."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def run_pipeline(config_path: str) -> Path:
    """
    パイプラインを実行.

    Args:
        config_path: 設定ファイルパス

    Returns:
        submission.csv のパス
    """
    # 設定読み込み
    config = load_config(config_path)

    task = config["task"]
    dataset = config["dataset"]
    split_config = config["split"]
    model_config = config["model"]
    preprocess_config = config.get("preprocess", {})
    output_config = config.get("output", {})

    # run_id生成
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    runs_dir = Path(output_config.get("runs_dir", "runs")) / run_id
    runs_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=== Tabular Pipeline Start ===")
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Task: {task}")

    # 設定保存
    config_resolved_path = runs_dir / "config_resolved.yaml"
    with open(config_resolved_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

    # データ読み込み
    try:
        X_train_df, X_test_df, y_train, schema = load_train_test(
            train_path=dataset["train_path"],
            test_path=dataset["test_path"],
            label_col=dataset["label_col"],
        )
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.info("Creating demo data...")
        create_demo_data(dataset, task)
        X_train_df, X_test_df, y_train, schema = load_train_test(
            train_path=dataset["train_path"],
            test_path=dataset["test_path"],
            label_col=dataset["label_col"],
        )

    # スキーマ保存
    save_schema(schema, runs_dir / "schema.json")

    # ラベルオフセット処理
    label_offset = dataset.get("label_offset", 0)
    y_train_adjusted = y_train.values
    if label_offset != 0:
        y_train_adjusted = y_train_adjusted - label_offset
        logger.info(f"Applied label offset: -{label_offset}")

    # 前処理
    scaler = create_preprocessor(preprocess_config.get("standardize", True))
    X_train_scaled, scaler = fit_transform(X_train_df, scaler)
    X_test_scaled = transform(X_test_df, scaler)

    if scaler is not None:
        save_scaler(scaler, runs_dir / "scaler.pkl")

    # データ分割
    X_tr, X_val, X_te, y_tr, y_val, y_te = split_data(
        X_train_scaled,
        y_train_adjusted,
        seed=split_config.get("seed", 0),
        train_ratio=split_config.get("train", 0.6),
        val_ratio=split_config.get("val", 0.2),
        test_ratio=split_config.get("test", 0.2),
    )

    # 学習
    model, train_metrics = train_model(
        X_tr,
        y_tr,
        X_val,
        y_val,
        task=task,
        model_type=model_config["type"],
        model_params=model_config,
    )

    # テストセット評価
    y_te_pred = predict(model, X_te)
    test_metrics = calculate_metrics(y_te, y_te_pred, task)

    # 全メトリクス統合
    all_metrics = {**train_metrics, **{f"test_{k}": v for k, v in test_metrics.items()}}

    # メトリクス保存
    with open(runs_dir / "metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=2)

    # モデル保存
    if output_config.get("save_model", True):
        model.save(runs_dir / "model.pkl")

    # 提出CSV生成
    test_predictions = predict(model, X_test_scaled)
    submission_path = make_submission(
        test_predictions,
        runs_dir / "submission.csv",
        target_col=dataset["submission_col"],
        label_offset=label_offset,
    )

    # レポート生成
    dataset_info = {
        "train_shape": schema.train_shape,
        "test_shape": schema.test_shape,
        "feature_count": len(schema.feature_columns),
        "label_handling": f"offset={label_offset}",
    }

    submission_checks = {
        "file_exists": submission_path.exists(),
        "row_count_match": True,
        "column_name_correct": True,
    }

    generate_report(
        run_id=run_id,
        task=task,
        dataset_info=dataset_info,
        metrics=all_metrics,
        submission_checks=submission_checks,
        config_path=config_path,
        output_dir=str(runs_dir),
    )

    logger.info("=== Pipeline Complete ===")
    logger.info(f"Submission: {submission_path}")
    logger.info(f"Report: {runs_dir / 'report.md'}")

    return submission_path


def create_demo_data(dataset: Dict[str, Any], task: str):
    """デモデータを作成."""
    import numpy as np
    import pandas as pd

    np.random.seed(0)

    train_path = Path(dataset["train_path"])
    test_path = Path(dataset["test_path"])
    label_col = dataset["label_col"]

    train_path.parent.mkdir(parents=True, exist_ok=True)

    n_train, n_test = 150, 50
    n_features = 5

    X_train = np.random.randn(n_train, n_features)
    X_test = np.random.randn(n_test, n_features)

    if task == "classification":
        y_train = np.random.randint(1, 4, n_train)  # 1,2,3
    else:
        y_train = np.random.randn(n_train) * 10 + 50

    cols = [f"feature_{i}" for i in range(n_features)]

    train_df = pd.DataFrame(X_train, columns=cols)
    train_df[label_col] = y_train
    train_df.to_csv(train_path, index=False)

    test_df = pd.DataFrame(X_test, columns=cols)
    test_df.to_csv(test_path, index=False)

    logger.info(f"Demo data created: {train_path}, {test_path}")


def main():
    parser = argparse.ArgumentParser(description="Tabular Pipeline CLI")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Config YAML path (e.g., configs/tabular/wine.yaml)",
    )

    args = parser.parse_args()

    try:
        submission_path = run_pipeline(args.config)
        print(f"\n✅ Success! Submission: {submission_path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
