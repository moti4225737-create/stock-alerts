import pytest

from models.story_correlation_result import (
    StoryCorrelationDecision,
    StoryCorrelationResult,
)


def test_result_supports_explicit_match_decision() -> None:
    result = StoryCorrelationResult(
        decision=StoryCorrelationDecision.MATCH,
        confidence=0.95,
        reason="The later event completes the earlier transaction.",
    )

    assert result.decision is StoryCorrelationDecision.MATCH
    assert result.is_correlated is True


def test_result_supports_explicit_no_match_decision() -> None:
    result = StoryCorrelationResult(
        decision=StoryCorrelationDecision.NO_MATCH,
        confidence=0.95,
        reason="The events belong to different stories.",
    )

    assert result.decision is StoryCorrelationDecision.NO_MATCH
    assert result.is_correlated is False


def test_result_supports_unresolved_decision() -> None:
    result = StoryCorrelationResult(
        decision=StoryCorrelationDecision.UNRESOLVED,
        confidence=0.40,
        reason=(
            "The available information is insufficient "
            "to establish story identity."
        ),
    )

    assert (
        result.decision
        is StoryCorrelationDecision.UNRESOLVED
    )
    assert result.is_correlated is False
    assert result.is_resolved is False


def test_match_and_no_match_are_resolved() -> None:
    match = StoryCorrelationResult(
        decision=StoryCorrelationDecision.MATCH,
        confidence=0.90,
        reason="Same story.",
    )

    no_match = StoryCorrelationResult(
        decision=StoryCorrelationDecision.NO_MATCH,
        confidence=0.90,
        reason="Different stories.",
    )

    assert match.is_resolved is True
    assert no_match.is_resolved is True


def test_unresolved_cannot_claim_full_confidence() -> None:
    with pytest.raises(
        ValueError,
        match="unresolved",
    ):
        StoryCorrelationResult(
            decision=StoryCorrelationDecision.UNRESOLVED,
            confidence=1.0,
            reason="Insufficient evidence.",
        )
