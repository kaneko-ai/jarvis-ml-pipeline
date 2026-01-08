"""
Tabular Models - Lightning Module

PyTorch Lightning による学習ループ
"""

from __future__ import annotations

import logging

import torch
import torch.nn as nn

try:
    import pytorch_lightning as pl
    LIGHTNING_AVAILABLE = True
except ImportError:
    LIGHTNING_AVAILABLE = False
    pl = None

from .mlp_torch import MLP

logger = logging.getLogger(__name__)


if LIGHTNING_AVAILABLE:
    class TabularLightningModule(pl.LightningModule):
        """Tabular用LightningModule.
        
        契約:
        - forward(x): logits（分類）/ y_pred（回帰）
        - training_step: loss + train metric
        - validation_step: loss + val metric（EarlyStopping監視対象）
        - test_step: test metric
        - configure_optimizers: Adam (lr=1e-3)
        """

        def __init__(
            self,
            input_dim: int,
            output_dim: int,
            task: str = "classification",
            hidden_dims: list = [128, 64],
            dropout: float = 0.3,
            use_bn: bool = True,
            lr: float = 1e-3,
        ):
            """初期化."""
            super().__init__()
            self.save_hyperparameters()

            self.task = task
            self.lr = lr

            self.model = MLP(
                input_dim=input_dim,
                output_dim=output_dim,
                hidden_dims=hidden_dims,
                dropout=dropout,
                use_bn=use_bn,
                task=task,
            )

            # Loss
            if task == "classification":
                self.loss_fn = nn.CrossEntropyLoss()
            else:
                self.loss_fn = nn.MSELoss()

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """順伝播."""
            return self.model(x)

        def training_step(self, batch, batch_idx) -> torch.Tensor:
            """学習ステップ."""
            x, y = batch
            y_hat = self(x)

            if self.task == "regression":
                y = y.view(-1, 1)
                y_hat = y_hat.view(-1, 1)

            loss = self.loss_fn(y_hat, y)

            # メトリクス
            if self.task == "classification":
                preds = torch.argmax(y_hat, dim=1)
                acc = (preds == y).float().mean()
                self.log("train_loss", loss, prog_bar=True)
                self.log("train_acc", acc, prog_bar=True)
            else:
                self.log("train_loss", loss, prog_bar=True)

            return loss

        def validation_step(self, batch, batch_idx) -> torch.Tensor:
            """検証ステップ."""
            x, y = batch
            y_hat = self(x)

            if self.task == "regression":
                y = y.view(-1, 1)
                y_hat = y_hat.view(-1, 1)

            loss = self.loss_fn(y_hat, y)

            if self.task == "classification":
                preds = torch.argmax(y_hat, dim=1)
                acc = (preds == y).float().mean()
                self.log("val_loss", loss, prog_bar=True)
                self.log("val_acc", acc, prog_bar=True)
            else:
                self.log("val_loss", loss, prog_bar=True)

            return loss

        def test_step(self, batch, batch_idx) -> torch.Tensor:
            """テストステップ."""
            x, y = batch
            y_hat = self(x)

            if self.task == "regression":
                y = y.view(-1, 1)
                y_hat = y_hat.view(-1, 1)

            loss = self.loss_fn(y_hat, y)

            if self.task == "classification":
                preds = torch.argmax(y_hat, dim=1)
                acc = (preds == y).float().mean()
                self.log("test_loss", loss)
                self.log("test_acc", acc)
            else:
                self.log("test_loss", loss)

            return loss

        def configure_optimizers(self):
            """オプティマイザ設定."""
            return torch.optim.Adam(self.parameters(), lr=self.lr)
else:
    TabularLightningModule = None
