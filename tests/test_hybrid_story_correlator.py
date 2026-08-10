from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationDecision,
    StoryCorrelationResult,
)
from product.hybrid_story_correlator import (
    HybridStoryCorrelator,
)


def make_event(
    title: str,
    summary: str,
    published_at: str,
) -> Event:
    return Event(
        symbol="ONDS",
        source="SEC",
        title=title,
        summary=summary,
        published_at=published_at,
        importance=8,
        sentiment="neutral",
        url="https://example.com/event",
    )


class StubDeterministicCorrelator:
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


class StubSemanticCorrelator:
    def __init__(
        self,
        result: StoryCorrelationResult,
    ) -> None:
        self.result = result
        self.calls = 0
        self.earlier_event = None
        self.current_event = None

    def correlate(
        self,
        earlier_event: Event,
        current_event: Event,
    ) -> StoryCorrelationResult:
        self.calls += 1
        self.earlier_event = earlier_event
        self.current_event = current_event
        return self.result


def make_events() -> tuple[Event, Event]:
    earlier = make_event(
        title="Strategic transaction announced",
        summary="The company announced a transaction.",
        published_at="2026-06-18",
    )

    current = make_event(
        title="Strategic update",
        summary="The company provided an update.",
        published_at="2026-07-10",
    )

    return earlier, current


def test_hybrid_preserves_definitive_positive_without_semantic_call() -> None:
    earlier, current = make_events()

    deterministic = StubDeterministicCorrelator(
        StoryCorrelationResult(
            is_correlated=True,
            confidence=1.0,
            reason="Deterministic positive match.",
        )
    )

    semantic = StubSemanticCorrelator(
        StoryCorrelationResult(
            is_correlated=False,
            confidence=0.9,
            reason="Semantic disagreement.",
        )
    )

    correlator = HybridStoryCorrelator(
        deterministic_correlator=deterministic,
        semantic_correlator=semantic,
    )

    result = correlator.correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert result.is_correlated
    assert result.confidence == 1.0
    assert semantic.calls == 0


def test_hybrid_preserves_definitive_negative_without_semantic_call() -> None:
    earlier, current = make_events()

    deterministic = StubDeterministicCorrelator(
        StoryCorrelationResult(
            is_correlated=False,
            confidence=0.0,
            reason="Deterministic negative match.",
        )
    )

    semantic = StubSemanticCorrelator(
        StoryCorrelationResult(
            is_correlated=True,
            confidence=0.9,
            reason="Semantic disagreement.",
        )
    )

    correlator = HybridStoryCorrelator(
        deterministic_correlator=deterministic,
        semantic_correlator=semantic,
    )

    result = correlator.correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert not result.is_correlated
    assert result.confidence == 0.0
    assert semantic.calls == 0


def test_hybrid_uses_semantic_fallback_only_when_uncertain() -> None:
    earlier, current = make_events()

    deterministic = StubDeterministicCorrelator(
        StoryCorrelationResult(
            decision=StoryCorrelationDecision.UNRESOLVED,
            confidence=0.5,
            reason="Insufficient deterministic context.",
        )
    )

    semantic_result = StoryCorrelationResult(
        is_correlated=True,
        confidence=0.9,
        reason=(
            "Semantic analysis identifies the current event "
            "as a continuation of the earlier transaction."
        ),
    )

    semantic = StubSemanticCorrelator(
        semantic_result
    )

    correlator = HybridStoryCorrelator(
        deterministic_correlator=deterministic,
        semantic_correlator=semantic,
    )

    result = correlator.correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert result is semantic_result
    assert deterministic.calls == 1
    assert semantic.calls == 1
    assert semantic.earlier_event is earlier
    assert semantic.current_event is current
