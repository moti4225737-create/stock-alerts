from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationResult,
)
from product.semantic_story_correlator import (
    SemanticStoryCorrelator,
)


class StubSemanticAnalyzer:
    def __init__(
        self,
        result: StoryCorrelationResult,
    ) -> None:
        self.result = result
        self.calls = 0
        self.earlier_event = None
        self.current_event = None

    def analyze(
        self,
        earlier_event: Event,
        current_event: Event,
    ) -> StoryCorrelationResult:
        self.calls += 1
        self.earlier_event = earlier_event
        self.current_event = current_event
        return self.result


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


def test_semantic_correlator_delegates_to_analyzer() -> None:
    earlier = make_event(
        title="Strategic transaction announced",
        summary=(
            "Ondas agreed to purchase a UK-based "
            "drone inspection business."
        ),
        published_at="2026-06-18",
    )

    current = make_event(
        title="Transaction closing",
        summary=(
            "The previously announced purchase of "
            "the inspection company has now closed."
        ),
        published_at="2026-08-10",
    )

    expected = StoryCorrelationResult(
        is_correlated=True,
        confidence=0.93,
        reason=(
            "Both events describe successive stages "
            "of the same acquisition."
        ),
    )

    analyzer = StubSemanticAnalyzer(expected)

    correlator = SemanticStoryCorrelator(
        analyzer=analyzer,
    )

    result = correlator.correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert result is expected
    assert analyzer.calls == 1
    assert analyzer.earlier_event is earlier
    assert analyzer.current_event is current


def test_semantic_correlator_preserves_negative_decision() -> None:
    earlier = make_event(
        title="Strategic transaction announced",
        summary="The company announced an acquisition.",
        published_at="2026-06-18",
    )

    current = make_event(
        title="Operational update",
        summary=(
            "The company announced a new customer "
            "deployment."
        ),
        published_at="2026-08-10",
    )

    expected = StoryCorrelationResult(
        is_correlated=False,
        confidence=0.88,
        reason=(
            "The events describe different business developments."
        ),
    )

    correlator = SemanticStoryCorrelator(
        analyzer=StubSemanticAnalyzer(expected),
    )

    result = correlator.correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert result is expected
    assert not result.is_correlated
    assert result.confidence == 0.88
