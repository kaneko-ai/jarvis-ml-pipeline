"""
Tabular Models Module
"""

from .baseline_lr import BaselineLogisticRegression
from .baseline_ridge import BaselineRidgeRegression

# PyTorch models (optional)
try:
    from .mlp_torch import MLP, create_mlp
    TORCH_AVAILABLE = True
except ImportError:
    MLP = None
    create_mlp = None
    TORCH_AVAILABLE = False

try:
    from .lightning_module import TabularLightningModule
    LIGHTNING_AVAILABLE = True
except ImportError:
    TabularLightningModule = None
    LIGHTNING_AVAILABLE = False

__all__ = [
    "BaselineLogisticRegression",
    "BaselineRidgeRegression",
    "MLP",
    "create_mlp",
    "TabularLightningModule",
    "TORCH_AVAILABLE",
    "LIGHTNING_AVAILABLE",
]

