from engines.signal_ranking_engine import SignalRankingEngine
from models.event import Event


def test_rank_orders_events_by_importance_descending():
    engine = SignalRankingEngine()

    low_importance = Event(
        symbol="AAPL",
        source="SEC",
        title="Low Importance Event",
        summary="Low importance event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=3,
        sentiment="neutral",
    )

    high_importance = Event(
        symbol="MSFT",
        source="SEC",
        title="High Importance Event",
        summary="High importance event summary",
        published_at="2026-08-01T09:00:00+00:00",
        importance=9,
        sentiment="neutral",
    )

    ranked = engine.rank([low_importance, high_importance])

    assert ranked == [high_importance, low_importance]


def test_rank_orders_equal_importance_by_published_at_descending():
    engine = SignalRankingEngine()

    older_event = Event(
        symbol="AAPL",
        source="SEC",
        title="Older Event",
        summary="Older event summary",
        published_at="2026-08-01T09:00:00+00:00",
        importance=5,
        sentiment="neutral",
    )

    newer_event = Event(
        symbol="MSFT",
        source="SEC",
        title="Newer Event",
        summary="Newer event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=5,
        sentiment="neutral",
    )

    ranked = engine.rank([older_event, newer_event])

    assert ranked == [newer_event, older_event]


def test_rank_returns_new_list_without_mutating_input():
    engine = SignalRankingEngine()

    low_importance = Event(
        symbol="AAPL",
        source="SEC",
        title="Low Importance Event",
        summary="Low importance event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=3,
        sentiment="neutral",
    )

    high_importance = Event(
        symbol="MSFT",
        source="SEC",
        title="High Importance Event",
        summary="High importance event summary",
        published_at="2026-08-01T09:00:00+00:00",
        importance=9,
        sentiment="neutral",
    )

    events = [low_importance, high_importance]

    ranked = engine.rank(events)

    assert ranked == [high_importance, low_importance]
    assert events == [low_importance, high_importance]


def test_rank_keeps_stable_order_when_importance_and_published_at_are_equal():
    engine = SignalRankingEngine()

    first_event = Event(
        symbol="AAPL",
        source="SEC",
        title="First Event",
        summary="First event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=5,
        sentiment="neutral",
    )

    second_event = Event(
        symbol="MSFT",
        source="SEC",
        title="Second Event",
        summary="Second event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=5,
        sentiment="neutral",
    )

    ranked = engine.rank([first_event, second_event])

    assert ranked == [first_event, second_event]


def test_rank_returns_empty_list_for_empty_input():
    engine = SignalRankingEngine()

    assert engine.rank([]) == []


def test_rank_returns_new_list_with_single_event():
    engine = SignalRankingEngine()

    event = Event(
        symbol="AAPL",
        source="SEC",
        title="Single Event",
        summary="Single event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=4,
        sentiment="neutral",
    )

    ranked = engine.rank([event])

    assert ranked == [event]
    assert ranked is not [event]