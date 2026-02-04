"""Tests for SPECTER2 Embedding."""

try:
    import sentence_transformers

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


from unittest.mock import MagicMock, patch

import numpy as np


def test_specter2_dimension():
    from jarvis_core.embeddings.specter2 import SPECTER2Embedding

    model = SPECTER2Embedding()
    assert model.dimension == 768


def test_specter2_embed_paper_format():
    # Test that embed_paper formats correctly
    with patch("jarvis_core.embeddings.specter2.SPECTER2Embedding._load_model") as mock_load:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1] * 768])
        mock_load.return_value = mock_model

        from jarvis_core.embeddings.specter2 import SPECTER2Embedding

        model = SPECTER2Embedding()

        model.embed_paper("Test Title", "Test Abstract")

        # Verify the format
        mock_model.encode.assert_called_once()
        call_args = mock_model.encode.call_args[0][0]
        assert "Test Title [SEP] Test Abstract" in call_args


def test_get_embedding_model_scientific():
    from jarvis_core.embeddings import get_embedding_model
    from jarvis_core.embeddings.specter2 import SPECTER2Embedding

    model = get_embedding_model("scientific")
    assert isinstance(model, SPECTER2Embedding)


def test_get_embedding_model_general():
    from jarvis_core.embeddings import get_embedding_model
    from jarvis_core.embeddings.sentence_transformer import SentenceTransformerEmbedding

    model = get_embedding_model("general")
    assert isinstance(model, SentenceTransformerEmbedding)
