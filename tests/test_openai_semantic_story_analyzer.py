from types import SimpleNamespace
from unittest.mock import Mock

from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationDecision,
)
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
    decision: StoryCorrelationDecision,
    confidence: float,
    reason: str,
):
    parsed = SimpleNamespace(
        decision=decision,
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


def make_analyzer(
    client: Mock,
) -> OpenAISemanticStoryAnalyzer:
    return OpenAISemanticStoryAnalyzer(
        client=client,
        model="gpt-5.6-luna",
        max_output_tokens=300,
    )


def test_analyzer_returns_match_decision() -> None:
    client = Mock()

    client.responses.parse.return_value = make_response(
        decision=StoryCorrelationDecision.MATCH,
        confidence=0.94,
        reason=(
            "The later event completes the "
            "previously announced acquisition."
        ),
    )

    analyzer = make_analyzer(client)

    result = analyzer.analyze(
        earlier_event=make_event(
            title="Strategic acquisition announced",
            summary=(
                "Ondas agreed to purchase Cyberhawk."
            ),
            published_at="2026-06-18",
        ),
        current_event=make_event(
            title="Transaction closing",
            summary=(
                "The previously announced purchase "
                "has now closed."
            ),
            published_at="2026-08-10",
        ),
    )

    assert result.decision is StoryCorrelationDecision.MATCH
    assert result.is_correlated is True
    assert result.is_resolved is True
    assert result.confidence == 0.94


def test_analyzer_returns_no_match_decision() -> None:
    client = Mock()

    client.responses.parse.return_value = make_response(
        decision=StoryCorrelationDecision.NO_MATCH,
        confidence=0.91,
        reason=(
            "The events describe different "
            "business developments."
        ),
    )

    analyzer = make_analyzer(client)

    result = analyzer.analyze(
        earlier_event=make_event(
            title="Acquisition announced",
            summary="The company announced an acquisition.",
            published_at="2026-06-18",
        ),
        current_event=make_event(
            title="Customer deployment",
            summary=(
                "The company announced a new "
                "customer deployment."
            ),
            published_at="2026-08-10",
        ),
    )

    assert (
        result.decision
        is StoryCorrelationDecision.NO_MATCH
    )
    assert result.is_correlated is False
    assert result.is_resolved is True
    assert result.confidence == 0.91


def test_analyzer_can_return_unresolved_when_evidence_is_insufficient() -> None:
    client = Mock()

    client.responses.parse.return_value = make_response(
        decision=StoryCorrelationDecision.UNRESOLVED,
        confidence=0.45,
        reason=(
            "The available descriptions do not establish "
            "whether the update belongs to the earlier story."
        ),
    )

    analyzer = make_analyzer(client)

    result = analyzer.analyze(
        earlier_event=make_event(
            title="Strategic transaction announced",
            summary=(
                "The company announced a strategic transaction."
            ),
            published_at="2026-06-18",
        ),
        current_event=make_event(
            title="Strategic update",
            summary="The company provided an update.",
            published_at="2026-07-10",
        ),
    )

    assert (
        result.decision
        is StoryCorrelationDecision.UNRESOLVED
    )
    assert result.is_correlated is False
    assert result.is_resolved is False
    assert result.confidence == 0.45
