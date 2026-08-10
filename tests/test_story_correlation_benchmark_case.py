import pytest

from models.event import Event
from models.story_correlation_benchmark_case import (
    StoryCorrelationBenchmarkCase,
)


def make_event(
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


def test_benchmark_case_preserves_expected_correlation() -> None:
    earlier = make_event(
        symbol="ONDS",
        title="Strategic acquisition announced",
        summary=(
            "Ondas agreed to purchase a UK-based "
            "drone inspection business."
        ),
        published_at="2026-06-18",
    )

    current = make_event(
        symbol="ONDS",
        title="Transaction closing",
        summary=(
            "The previously announced purchase of "
            "the inspection company has now closed."
        ),
        published_at="2026-08-10",
    )

    case = StoryCorrelationBenchmarkCase(
        name="same acquisition different wording",
        earlier_event=earlier,
        current_event=current,
        expected_is_correlated=True,
    )

    assert case.name == (
        "same acquisition different wording"
    )
    assert case.expected_is_correlated is True


def test_benchmark_case_rejects_blank_name() -> None:
    event = make_event(
        symbol="ONDS",
        title="Event",
        summary="Summary",
        published_at="2026-08-10",
    )

    with pytest.raises(ValueError, match="name"):
        StoryCorrelationBenchmarkCase(
            name=" ",
            earlier_event=event,
            current_event=event,
            expected_is_correlated=True,
        )


def test_benchmark_case_rejects_different_symbols() -> None:
    earlier = make_event(
        symbol="ONDS",
        title="Event",
        summary="Summary",
        published_at="2026-08-10",
    )

    current = make_event(
        symbol="LQDA",
        title="Event",
        summary="Summary",
        published_at="2026-08-11",
    )

    with pytest.raises(
        ValueError,
        match="same symbol",
    ):
        StoryCorrelationBenchmarkCase(
            name="invalid cross-symbol case",
            earlier_event=earlier,
            current_event=current,
            expected_is_correlated=False,
        )
