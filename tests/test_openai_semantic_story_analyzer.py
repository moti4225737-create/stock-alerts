from types import SimpleNamespace
from unittest.mock import Mock

from models.event import Event
from product.openai_semantic_story_analyzer import (
    OpenAISemanticStoryAnalyzer,
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


def make_response(
    is_correlated: bool,
    confidence: float,
    reason: str,
):
    parsed = SimpleNamespace(
        is_correlated=is_correlated,
        confidence=confidence,
        reason=reason,
    )

    content = SimpleNamespace(
        parsed=parsed,
    )

    message = SimpleNamespace(
        type="message",
        content=(content,),
    )

    return SimpleNamespace(
        output=(message,),
    )


def test_analyzer_returns_structured_positive_decision() -> None:
    client = Mock()

    client.responses.parse.return_value = make_response(
        is_correlated=True,
        confidence=0.94,
        reason=(
            "The second event explicitly refers to the "
            "previously announced acquisition."
        ),
    )

    analyzer = OpenAISemanticStoryAnalyzer(
        client=client,
        model="gpt-5.6-luna",
        max_output_tokens=300,
    )

    earlier = make_event(
        title="Strategic acquisition announced",
        summary=(
            "Ondas agreed to purchase the UK-based "
            "drone inspection company Cyberhawk."
        ),
        published_at="2026-06-18",
    )

    current = make_event(
        title="Transaction closing",
        summary=(
            "The previously announced purchase of the "
            "inspection company has now closed."
        ),
        published_at="2026-08-10",
    )

    result = analyzer.analyze(
        earlier_event=earlier,
        current_event=current,
    )

    assert result.is_correlated is True
    assert result.confidence == 0.94
    assert result.reason


def test_analyzer_returns_structured_negative_decision() -> None:
    client = Mock()

    client.responses.parse.return_value = make_response(
        is_correlated=False,
        confidence=0.72,
        reason=(
            "The available descriptions do not provide "
            "enough evidence that the update refers to "
            "the earlier transaction."
        ),
    )

    analyzer = OpenAISemanticStoryAnalyzer(
        client=client,
        model="gpt-5.6-luna",
        max_output_tokens=300,
    )

    earlier = make_event(
        title="Strategic transaction announced",
        summary=(
            "The company announced a strategic transaction."
        ),
        published_at="2026-06-18",
    )

    current = make_event(
        title="Strategic update",
        summary="The company provided an update.",
        published_at="2026-07-10",
    )

    result = analyzer.analyze(
        earlier_event=earlier,
        current_event=current,
    )

    assert result.is_correlated is False
    assert result.confidence == 0.72
    assert result.reason
