from decimal import Decimal
from datetime import datetime, timezone
from dataclasses import FrozenInstanceError

import pytest

from models.macro_event import MacroEvent, MacroEventType, MacroEventStatus, MacroSurpriseDirection
from models.macro_region import MacroRegion


def build_macro_event(**overrides):
    defaults = {
        "event_id": "event-001",
        "event_type": MacroEventType.CPI,
        "name": "Consumer Price Index",
        "country": MacroRegion.US,
        "scheduled_at": datetime(2026, 7, 15, 12, 30, tzinfo=timezone.utc),
        "status": MacroEventStatus.SCHEDULED,
        "actual": Decimal("3.2"),
        "forecast": Decimal("3.1"),
        "previous": Decimal("3.0"),
        "unit": "%",
        "source": "FRED",
        "source_url": "https://example.com/event",
    }
    defaults.update(overrides)
    return MacroEvent(**defaults)


def test_macro_event_creates_with_expected_values() -> None:
    event = build_macro_event()

    assert event.event_id == "event-001"
    assert event.event_type is MacroEventType.CPI
    assert event.name == "Consumer Price Index"
    assert event.country == "US"
    assert event.scheduled_at == datetime(2026, 7, 15, 12, 30, tzinfo=timezone.utc)
    assert event.status is MacroEventStatus.SCHEDULED
    assert event.actual == Decimal("3.2")
    assert event.forecast == Decimal("3.1")
    assert event.previous == Decimal("3.0")
    assert event.unit == "%"
    assert event.source == "FRED"
    assert event.source_url == "https://example.com/event"


def test_macro_event_requires_timezone_aware_datetime() -> None:
    with pytest.raises(ValueError, match="timezone"):
        build_macro_event(scheduled_at=datetime(2026, 7, 15, 12, 30))


def test_macro_event_rejects_blank_required_strings() -> None:
    with pytest.raises(ValueError, match="event_id"):
        build_macro_event(event_id="   ")

    with pytest.raises(ValueError, match="name"):
        build_macro_event(name="  ")

    with pytest.raises(ValueError, match="country"):
        build_macro_event(country="\t")

    with pytest.raises(ValueError, match="source"):
        build_macro_event(source="")


def test_macro_event_requires_decimal_or_none_for_numeric_fields() -> None:
    with pytest.raises(TypeError, match="actual"):
        build_macro_event(actual=3.2)

    with pytest.raises(TypeError, match="forecast"):
        build_macro_event(forecast=1.23)

    with pytest.raises(TypeError, match="previous"):
        build_macro_event(previous=0.0)


def test_macro_event_calculates_surprise_direction_and_value() -> None:
    event = build_macro_event(actual=Decimal("3.4"), forecast=Decimal("3.1"))
    assert event.surprise_direction is MacroSurpriseDirection.ABOVE_FORECAST
    assert event.surprise_value == Decimal("0.3")

    below_forecast = build_macro_event(actual=Decimal("3.0"), forecast=Decimal("3.1"))
    assert below_forecast.surprise_direction is MacroSurpriseDirection.BELOW_FORECAST
    assert below_forecast.surprise_value == Decimal("-0.1")

    in_line = build_macro_event(actual=Decimal("3.1"), forecast=Decimal("3.1"))
    assert in_line.surprise_direction is MacroSurpriseDirection.IN_LINE
    assert in_line.surprise_value == Decimal("0")

    unknown = build_macro_event(actual=None, forecast=Decimal("3.1"))
    assert unknown.surprise_direction is MacroSurpriseDirection.UNKNOWN
    assert unknown.surprise_value is None


def test_macro_event_is_immutable() -> None:
    event = build_macro_event()

    with pytest.raises(FrozenInstanceError):
        event.name = "Changed"


def test_macro_event_metadata_is_immutable_and_defensively_copied() -> None:
    source_metadata = {"source_type": "official"}
    event = build_macro_event(metadata=source_metadata)

    source_metadata["source_type"] = "changed"

    assert event.metadata["source_type"] == "official"

    with pytest.raises(TypeError):
        event.metadata["source_type"] = "blocked"
