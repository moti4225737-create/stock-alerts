from models.story_correlation_result import (
    StoryCorrelationDecision,
    StoryCorrelationResult,
)


def test_ambiguous_result_is_explicitly_unresolved() -> None:
    result = StoryCorrelationResult(
        decision=StoryCorrelationDecision.UNRESOLVED,
        confidence=0.5,
        reason="Insufficient evidence.",
    )

    assert result.is_resolved is False
    assert result.is_correlated is False
