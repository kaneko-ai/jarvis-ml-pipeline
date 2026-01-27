"""
Tabular Models - PyTorch MLP

分類/回帰共通MLP（hidden, dropout, bn設定可能）
"""

from __future__ import annotations

import logging
from typing import List

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class MLP(nn.Module):
    """Multi-Layer Perceptron for tabular data."""

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden_dims: List[int] = [128, 64],
        dropout: float = 0.3,
        use_bn: bool = True,
        task: str = "classification",
    ):
        """
        初期化.

        Args:
            input_dim: 入力次元
            output_dim: 出力次元（分類ならクラス数、回帰なら1）
            hidden_dims: 隠れ層の次元リスト
            dropout: ドロップアウト率
            use_bn: BatchNormを使うか
            task: classification or regression
        """
        super().__init__()

        self.task = task
        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            if use_bn:
                layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, output_dim))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """順伝播."""
        return self.network(x)


def create_mlp(
    input_dim: int,
    output_dim: int,
    config: dict,
) -> MLP:
    """
    設定からMLPを作成.

    Args:
        input_dim: 入力次元
        output_dim: 出力次元
        config: モデル設定

    Returns:
        MLP
    """
    return MLP(
        input_dim=input_dim,
        output_dim=output_dim,
        hidden_dims=config.get("hidden", [128, 64]),
        dropout=config.get("dropout", 0.3),
        use_bn=config.get("bn", True),
        task=config.get("task", "classification"),
    )
