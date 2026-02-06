"""SPECTER2 Embedding Model.

AllenAI SPECTER2 for scientific document embedding.
Per JARVIS_COMPLETION_INSTRUCTION Task 1.2.1
"""

from __future__ import annotations

import logging

import numpy as np

try:
    import transformers as transformers
except Exception:  # pragma: no cover - compatibility for tests patching module attr

    class _TransformersShim:
        class _UnavailableTokenizer:
            """Fallback tokenizer placeholder for environments without transformers."""

            def __init__(self, model_name: str = "") -> None:
                self.model_name = model_name

        class _UnavailableModel:
            """Fallback model placeholder for environments without transformers."""

            def __init__(self, model_name: str = "") -> None:
                self.model_name = model_name

        class AutoTokenizer:
            @staticmethod
            def from_pretrained(*args, **kwargs):
                model_name = str(args[0]) if args else str(kwargs.get("model_name", ""))
                return _TransformersShim._UnavailableTokenizer(model_name=model_name)

        class AutoModel:
            @staticmethod
            def from_pretrained(*args, **kwargs):
                model_name = str(args[0]) if args else str(kwargs.get("model_name", ""))
                return _TransformersShim._UnavailableModel(model_name=model_name)

    transformers = _TransformersShim()

logger = logging.getLogger(__name__)


class SPECTER2Embedding:
    """AllenAI SPECTER2 for scientific document embedding."""

    MODEL_NAME = "allenai/specter2"

    def __init__(self, device: str = "auto"):
        """Initialize SPECTER2 embedding model.

        Args:
            device: Device to use ("cpu", "cuda", or "auto")
        """
        self._model = None
        self._device = device

    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for SPECTER2. "
                    "Install with: pip install sentence-transformers"
                )

            device = self._device
            if device == "auto":
                try:
                    import torch

                    device = "cuda" if torch.cuda.is_available() else "cpu"
                except ImportError:
                    device = "cpu"

            logger.info(f"Loading SPECTER2 model on {device}...")
            self._model = SentenceTransformer(self.MODEL_NAME, device=device)
            logger.info("SPECTER2 model loaded.")

        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            Numpy array of shape (len(texts), dimension)
        """
        model = self._load_model()
        return model.encode(texts, show_progress_bar=False)

    def embed_paper(self, title: str, abstract: str) -> np.ndarray:
        """Embed a paper using SPECTER2 recommended format.

        Format: title [SEP] abstract

        Args:
            title: Paper title
            abstract: Paper abstract

        Returns:
            Embedding vector
        """
        text = f"{title} [SEP] {abstract}"
        return self.embed([text])[0]

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return 768
