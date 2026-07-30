from dataclasses import FrozenInstanceError

import pytest

from models.company_intelligence import CompanyIntelligence
from models.event import Event


def _build_event(
    symbol: str = "LQDA",
    source: str = "FDA",
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


def test_creates_company_intelligence():
    event = _build_event()

    intelligence = CompanyIntelligence(
        symbol="LQDA",
        events=(event,),
        metadata={
            "sector": "Healthcare",
        },
    )

    assert intelligence.symbol == "LQDA"
    assert intelligence.events == (event,)
    assert intelligence.metadata["sector"] == "Healthcare"


def test_normalizes_symbol():
    intelligence = CompanyIntelligence(
        symbol=" lqda ",
    )

    assert intelligence.symbol == "LQDA"


def test_events_are_stored_as_tuple():
    event = _build_event()

    intelligence = CompanyIntelligence(
        symbol="LQDA",
        events=[event],
    )

    assert intelligence.events == (event,)
    assert isinstance(intelligence.events, tuple)


def test_metadata_is_immutable():
    metadata = {
        "sector": "Healthcare",
    }

    intelligence = CompanyIntelligence(
        symbol="LQDA",
        metadata=metadata,
    )

    metadata["sector"] = "Technology"

    assert intelligence.metadata["sector"] == "Healthcare"

    with pytest.raises(TypeError):
        intelligence.metadata["sector"] = "Technology"


def test_company_intelligence_is_immutable():
    intelligence = CompanyIntelligence(
        symbol="LQDA",
    )

    with pytest.raises(FrozenInstanceError):
        intelligence.symbol = "NVDA"


def test_rejects_empty_symbol():
    with pytest.raises(
        ValueError,
        match="symbol must not be empty",
    ):
        CompanyIntelligence(
            symbol="   ",
        )