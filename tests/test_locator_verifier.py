"""Tests for locator verification."""

from jarvis_core.evidence.locator_verifier import verify_locator


def test_verify_locator_exact_match():
    locator = "CD73 is expressed in immune cells"
    source_text = "... CD73 is expressed in immune cells and stromal cells."

    result = verify_locator(locator, source_text)

    assert result.is_valid is True
    assert result.match_ratio == 1.0
    assert result.matched_span == locator


def test_verify_locator_fuzzy_match():
    locator = "increases survival rate"
    source_text = "The treatment increases survival rates in patients."

    result = verify_locator(locator, source_text)

    assert result.is_valid is True
    assert result.match_ratio >= 0.8
    assert result.matched_span


def test_verify_locator_no_match():
    locator = "unrelated phrase"
    source_text = "The dataset contains no matching snippet."

    result = verify_locator(locator, source_text)

    assert result.is_valid is False
    assert result.match_ratio < 0.8
