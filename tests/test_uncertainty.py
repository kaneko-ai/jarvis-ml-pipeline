"""Tests for uncertainty label determination."""

import pytest

from jarvis_core.evidence.uncertainty import determine_uncertainty_label


@pytest.mark.parametrize(
    ("strength", "expected"),
    [
        (1.0, "確定"),
        (0.95, "確定"),
        (0.94, "高信頼"),
        (0.80, "高信頼"),
        (0.79, "要注意"),
        (0.60, "要注意"),
        (0.59, "推測"),
        (0.0, "推測"),
    ],
)
def test_determine_uncertainty_label_boundaries(strength, expected):
    assert determine_uncertainty_label(strength) == expected
