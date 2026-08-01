from datetime import datetime, timezone
from decimal import Decimal

from models.macro_event import MacroEvent
from models.macro_event_status import MacroEventStatus
from models.macro_event_type import MacroEventType
from models.macro_region import MacroRegion
from modules.macro_calendar_provider import MacroCalendarProvider
from modules.static_macro_calendar_provider import StaticMacroCalendarProvider


def test_provider_implements_macro_calendar_provider() -> None:
    provider = StaticMacroCalendarProvider()

    assert isinstance(provider, MacroCalendarProvider)


def test_fetch_upcoming_events_returns_deterministic_collection() -> None:
    provider = StaticMacroCalendarProvider()

    first = provider.fetch_upcoming_events(regions=[MacroRegion.US], days_ahead=365)
    second = provider.fetch_upcoming_events(regions=[MacroRegion.US], days_ahead=365)

    assert isinstance(first, list)
    assert all(isinstance(event, MacroEvent) for event in first)
    assert [event.event_id for event in first] == [event.event_id for event in second]
    assert [event.scheduled_at for event in first] == [event.scheduled_at for event in second]


def test_fetch_upcoming_events_contains_expected_macro_events() -> None:
    provider = StaticMacroCalendarProvider()

    events = provider.fetch_upcoming_events(regions=[MacroRegion.US], days_ahead=365)
    names = {event.name for event in events}

    assert "FOMC Rate Decision" in names
    assert "CPI" in names
    assert "Core CPI" in names
    assert "PPI" in names
    assert "Core PPI" in names
    assert "Non-Farm Payrolls" in names
    assert "Unemployment Rate" in names
    assert "Core PCE" in names


def test_fetch_upcoming_events_are_sorted_and_unique() -> None:
    provider = StaticMacroCalendarProvider()

    events = provider.fetch_upcoming_events(regions=[MacroRegion.US], days_ahead=365)
    event_ids = [event.event_id for event in events]
    scheduled_at = [event.scheduled_at for event in events]

    assert scheduled_at == sorted(scheduled_at)
    assert len(event_ids) == len(set(event_ids))


def test_fetch_upcoming_events_use_expected_types_and_regions() -> None:
    provider = StaticMacroCalendarProvider()

    events = provider.fetch_upcoming_events(regions=[MacroRegion.US], days_ahead=365)
    event_map = {event.name: event for event in events}

    assert event_map["FOMC Rate Decision"].event_type is MacroEventType.INTEREST_RATE_DECISION
    assert event_map["FOMC Rate Decision"].country is MacroRegion.US
    assert event_map["CPI"].event_type is MacroEventType.CPI
    assert event_map["CPI"].country is MacroRegion.US
    assert event_map["Core CPI"].event_type is MacroEventType.CORE_CPI
    assert event_map["Core CPI"].country is MacroRegion.US
    assert event_map["PPI"].event_type is MacroEventType.PPI
    assert event_map["PPI"].country is MacroRegion.US
    assert event_map["Core PPI"].event_type is MacroEventType.CORE_PPI
    assert event_map["Core PPI"].country is MacroRegion.US
    assert event_map["Non-Farm Payrolls"].event_type is MacroEventType.NONFARM_PAYROLLS
    assert event_map["Non-Farm Payrolls"].country is MacroRegion.US
    assert event_map["Unemployment Rate"].event_type is MacroEventType.UNEMPLOYMENT_RATE
    assert event_map["Unemployment Rate"].country is MacroRegion.US
    assert event_map["Core PCE"].event_type is MacroEventType.CORE_PCE
    assert event_map["Core PCE"].country is MacroRegion.US


def test_fetch_upcoming_events_preserves_expected_status_and_metadata_defaults() -> None:
    provider = StaticMacroCalendarProvider()

    events = provider.fetch_upcoming_events(regions=[MacroRegion.US], days_ahead=365)

    for event in events:
        assert event.status is MacroEventStatus.SCHEDULED
        assert event.actual is not None
        assert event.forecast is not None
        assert event.previous is not None
        assert event.unit is not None
        assert event.source
        assert event.scheduled_at.tzinfo is not None
