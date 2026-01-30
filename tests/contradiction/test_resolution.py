"""Tests for Contradiction Resolution."""

from jarvis_core.contradiction.resolution import (
    ContradictionResolver,
    ResolutionStrategy,
    ResolutionSuggestion,
)


def test_resolution_strategy_enum():
    assert ResolutionStrategy.METHODOLOGY.value == "methodology"
    assert ResolutionStrategy.POPULATION.value == "population"


def test_rule_based_returns_suggestion():
    resolver = ContradictionResolver(use_llm=False)

    claim_a = "Using PCR method, we found 80% positive rate"
    claim_b = "With ELISA technique, only 50% tested positive"

    suggestion = resolver.suggest_resolution(claim_a, claim_b)

    # Should return some valid strategy
    assert isinstance(suggestion, ResolutionSuggestion)
    assert suggestion.confidence > 0


def test_rule_based_with_numeric_difference():
    resolver = ContradictionResolver(use_llm=False)

    claim_a = "The efficacy was 90% in the treatment group"
    claim_b = "Only 45% efficacy was observed"

    suggestion = resolver.suggest_resolution(claim_a, claim_b)

    # Numeric differences should trigger MEASURE strategy
    assert suggestion.strategy == ResolutionStrategy.MEASURE


def test_unknown_strategy():
    resolver = ContradictionResolver(use_llm=False)

    claim_a = "The sky is blue"
    claim_b = "The sky is red"

    suggestion = resolver.suggest_resolution(claim_a, claim_b)

    # Should return UNKNOWN for unrecognized patterns
    assert suggestion.strategy == ResolutionStrategy.UNKNOWN


def test_suggestion_has_recommended_action():
    resolver = ContradictionResolver(use_llm=False)

    suggestion = resolver.suggest_resolution("claim a", "claim b")

    assert suggestion.recommended_action is not None
    assert len(suggestion.recommended_action) > 0