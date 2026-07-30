from models.event import Event
from models.intelligence_aggregator import IntelligenceAggregator


def _build_event(
    symbol: str,
    source: str = "TestProvider",
) -> Event:
    return Event(
        source=source,
        symbol=symbol,
        title="Test Event",
        summary="Test summary",
        url="https://example.com/event",
        published_at="2026-07-01",
        importance=5,
        sentiment="neutral",
    )


def test_groups_events_by_symbol():
    aggregator = IntelligenceAggregator()

    events = [
        _build_event(
            symbol="LQDA",
            source="FDA",
        ),
        _build_event(
            symbol="LQDA",
            source="ClinicalTrials",
        ),
        _build_event(
            symbol="NVDA",
            source="SEC",
        ),
    ]

    intelligence = aggregator.aggregate(events)

    assert set(intelligence.keys()) == {
        "LQDA",
        "NVDA",
    }

    assert len(intelligence["LQDA"]) == 2
    assert len(intelligence["NVDA"]) == 1

    assert intelligence["LQDA"][0].source == "FDA"
    assert (
        intelligence["LQDA"][1].source
        == "ClinicalTrials"
    )


def test_normalizes_symbols_and_skips_empty_symbols():
    aggregator = IntelligenceAggregator()

    events = [
        _build_event(symbol=" lqda "),
        _build_event(symbol="LQDA"),
        _build_event(symbol="   "),
    ]

    intelligence = aggregator.aggregate(events)

    assert set(intelligence.keys()) == {"LQDA"}
    assert len(intelligence["LQDA"]) == 2