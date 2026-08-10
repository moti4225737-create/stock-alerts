from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationDecision,
    StoryCorrelationResult,
)
from product.hybrid_story_correlator import (
    HybridStoryCorrelator,
)


class StubCorrelator:
    def __init__(
        self,
        result: StoryCorrelationResult,
    ) -> None:
        self.result = result
        self.calls = 0

    def correlate(
        self,
        earlier_event: Event,
        current_event: Event,
    ) -> StoryCorrelationResult:
        self.calls += 1
        return self.result


def make_event() -> Event:
    return Event(
        symbol="ONDS",
        source="Test",
        title="Event",
        summary="Summary",
        published_at="2026-08-10",
        importance=8,
        sentiment="neutral",
        url="https://example.com/event",
    )


def test_hybrid_uses_semantic_only_for_unresolved_decision() -> None:
    event = make_event()

    deterministic = StubCorrelator(
        StoryCorrelationResult(
            decision=StoryCorrelationDecision.UNRESOLVED,
            confidence=0.5,
            reason="Insufficient deterministic evidence.",
        )
    )

    semantic_result = StoryCorrelationResult(
        decision=StoryCorrelationDecision.MATCH,
        confidence=0.92,
        reason="Semantic evidence links the events.",
    )

    semantic = StubCorrelator(semantic_result)

    hybrid = HybridStoryCorrelator(
        deterministic_correlator=deterministic,
        semantic_correlator=semantic,
    )

    result = hybrid.correlate(
        earlier_event=event,
        current_event=event,
    )

    assert result is semantic_result
    assert deterministic.calls == 1
    assert semantic.calls == 1


def test_hybrid_does_not_call_semantic_for_resolved_decision() -> None:
    event = make_event()

    deterministic_result = StoryCorrelationResult(
        decision=StoryCorrelationDecision.NO_MATCH,
        confidence=0.7,
        reason="Different story domains.",
    )

    deterministic = StubCorrelator(
        deterministic_result
    )

    semantic = StubCorrelator(
        StoryCorrelationResult(
            decision=StoryCorrelationDecision.MATCH,
            confidence=0.99,
            reason="Should never be used.",
        )
    )

    hybrid = HybridStoryCorrelator(
        deterministic_correlator=deterministic,
        semantic_correlator=semantic,
    )

    result = hybrid.correlate(
        earlier_event=event,
        current_event=event,
    )

    assert result is deterministic_result
    assert semantic.calls == 0
