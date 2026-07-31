import pytest

from models.event import Event
from models.intelligence_timeline import IntelligenceTimeline


def _build_event(
    symbol: str,
    title: str,
    published_at: str,
    importance: int = 1,
) -> Event:
    return Event(
        source="TestProvider",
        symbol=symbol,
        title=title,
        summary=f"Summary for {title}",
        url="https://example.com/event",
        published_at=published_at,
        importance=importance,
        sentiment="neutral",
    )


def test_timeline_normalizes_symbol_and_orders_events_chronologically() -> None:
    older_event = _build_event(
        symbol="LQDA",
        title="Earlier Event",
        published_at="2026-07-01",
        importance=2,
    )
    newer_event = _build_event(
        symbol=" lqda ",
        title="Later Event",
        published_at="2026-07-03T12:30:00Z",
        importance=5,
    )

    timeline = IntelligenceTimeline(
        symbol=" lqda ",
        events=[newer_event, older_event],
    )

    assert timeline.symbol == "LQDA"
    assert timeline.events == (older_event, newer_event)
    assert timeline.latest_event is newer_event


def test_timeline_rejects_empty_published_at_values() -> None:
    with pytest.raises(ValueError, match="published_at"):
        IntelligenceTimeline(
            symbol="LQDA",
            events=[
                _build_event(
                    symbol="LQDA",
                    title="Missing Date",
                    published_at="",
                )
            ],
        )


def test_timeline_rejects_invalid_published_at_values() -> None:
    with pytest.raises(ValueError, match="published_at"):
        IntelligenceTimeline(
            symbol="LQDA",
            events=[
                _build_event(
                    symbol="LQDA",
                    title="Bad Date",
                    published_at="not-a-date",
                )
            ],
        )


def test_timeline_accepts_timezone_offset_datetime_strings() -> None:
    event = _build_event(
        symbol="LQDA",
        title="Offset Event",
        published_at="2026-07-01T12:30:00-04:00",
    )

    timeline = IntelligenceTimeline(symbol="LQDA", events=[event])

    assert timeline.latest_event is event
