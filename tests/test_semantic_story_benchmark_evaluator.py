from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationDecision,
)
from product.semantic_story_benchmark_evaluator import (
    SemanticStoryBenchmarkCase,
    SemanticStoryBenchmarkEvaluator,
)


def event(
    symbol: str,
    title: str,
    summary: str,
    published_at: str,
) -> Event:
    return Event(
        symbol=symbol,
        source="Benchmark",
        title=title,
        summary=summary,
        published_at=published_at,
        importance=8,
        sentiment="neutral",
        url="https://example.com/event",
    )


def test_evaluator_accepts_match_case() -> None:
    case = SemanticStoryBenchmarkCase(
        name="implicit acquisition continuation",
        earlier_event=event(
            "ONDS",
            "Strategic acquisition announced",
            (
                "Ondas agreed to purchase the UK-based "
                "drone inspection company Cyberhawk."
            ),
            "2026-06-18",
        ),
        current_event=event(
            "ONDS",
            "Transaction closing",
            (
                "The previously announced purchase of the "
                "inspection company has now closed."
            ),
            "2026-08-10",
        ),
        expected_decision=StoryCorrelationDecision.MATCH,
    )

    assert case.expected_decision is StoryCorrelationDecision.MATCH


def test_evaluator_accepts_no_match_case() -> None:
    case = SemanticStoryBenchmarkCase(
        name="same asset different domain",
        earlier_event=event(
            "LQDA",
            "FDA approves YUTREPIA",
            "FDA approved YUTREPIA.",
            "2025-05-23",
        ),
        current_event=event(
            "LQDA",
            "YUTREPIA patent litigation update",
            (
                "The company reported developments in "
                "patent litigation involving YUTREPIA."
            ),
            "2026-03-31",
        ),
        expected_decision=StoryCorrelationDecision.NO_MATCH,
    )

    assert case.expected_decision is StoryCorrelationDecision.NO_MATCH


def test_evaluator_accepts_unresolved_case() -> None:
    case = SemanticStoryBenchmarkCase(
        name="insufficient strategic context",
        earlier_event=event(
            "ONDS",
            "Strategic transaction announced",
            "The company announced a strategic transaction.",
            "2026-06-18",
        ),
        current_event=event(
            "ONDS",
            "Strategic update",
            "The company provided an update.",
            "2026-07-10",
        ),
        expected_decision=StoryCorrelationDecision.UNRESOLVED,
    )

    assert (
        case.expected_decision
        is StoryCorrelationDecision.UNRESOLVED
    )


def test_evaluator_scores_exact_decision_match() -> None:
    evaluator = SemanticStoryBenchmarkEvaluator()

    assert evaluator.is_correct(
        expected=StoryCorrelationDecision.MATCH,
        actual=StoryCorrelationDecision.MATCH,
    )

    assert not evaluator.is_correct(
        expected=StoryCorrelationDecision.UNRESOLVED,
        actual=StoryCorrelationDecision.NO_MATCH,
    )
