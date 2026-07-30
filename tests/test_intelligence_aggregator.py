from models.company_intelligence import CompanyIntelligence
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


def test_aggregates_events_into_company_intelligence():
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

    assert isinstance(
        intelligence["LQDA"],
        CompanyIntelligence,
    )

    assert isinstance(
        intelligence["NVDA"],
        CompanyIntelligence,
    )

    assert intelligence["LQDA"].symbol == "LQDA"
    assert intelligence["NVDA"].symbol == "NVDA"

    assert len(intelligence["LQDA"].events) == 2
    assert len(intelligence["NVDA"].events) == 1

    assert intelligence["LQDA"].events[0].source == "FDA"
    assert (
        intelligence["LQDA"].events[1].source
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

    assert intelligence["LQDA"].symbol == "LQDA"
    assert len(intelligence["LQDA"].events) == 2