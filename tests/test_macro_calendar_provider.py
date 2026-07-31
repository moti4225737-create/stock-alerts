from datetime import datetime, timedelta, timezone
from decimal import Decimal

from models.macro_event import MacroEvent
from models.macro_event_status import MacroEventStatus
from models.macro_event_type import MacroEventType
from models.macro_region import MacroRegion
from models.macro_surprise_direction import MacroSurpriseDirection
from modules.macro_calendar_provider import MacroCalendarProvider


class FakeMacroCalendarProvider(MacroCalendarProvider):
    def fetch_upcoming_events(
        self,
        *,
        regions: list[MacroRegion] | None = None,
        days_ahead: int = 30,
    ) -> list[MacroEvent]:
        return []


def _build_event(
    event_id: str,
    scheduled_at: datetime,
    region: MacroRegion,
    status: MacroEventStatus = MacroEventStatus.SCHEDULED,
) -> MacroEvent:
    return MacroEvent(
        event_id=event_id,
        event_type=MacroEventType.CPI,
        name=f"Event {event_id}",
        country=region,
        scheduled_at=scheduled_at,
        status=status,
        actual=Decimal("3.2"),
        forecast=Decimal("3.1"),
        previous=Decimal("3.0"),
        unit="%",
        source="FRED",
        source_url="https://example.com/event",
    )


def test_fetch_upcoming_events_returns_macro_events_list() -> None:
    provider = FakeMacroCalendarProvider()

    events = provider.fetch_upcoming_events(regions=[MacroRegion.US], days_ahead=14)

    assert isinstance(events, list)
    assert events == []


def test_fetch_upcoming_events_filters_by_region_and_days_ahead() -> None:
    provider = FakeMacroCalendarProvider()
    now = datetime.now(timezone.utc)

    events = [
        _build_event("e-1", now + timedelta(days=2), MacroRegion.US),
        _build_event("e-2", now + timedelta(days=5), MacroRegion.EU),
        _build_event("e-3", now + timedelta(days=10), MacroRegion.US),
        _build_event("e-4", now + timedelta(days=20), MacroRegion.US),
    ]

    filtered = provider._filter_events(events, regions=[MacroRegion.US], days_ahead=7)

    assert [event.event_id for event in filtered] == ["e-1", "e-3"]


def test_fetch_upcoming_events_excludes_cancelled_events() -> None:
    provider = FakeMacroCalendarProvider()
    now = datetime.now(timezone.utc)

    events = [
        _build_event("e-1", now + timedelta(days=1), MacroRegion.US),
        _build_event(
            "e-2",
            now + timedelta(days=2),
            MacroRegion.US,
            status=MacroEventStatus.CANCELLED,
        ),
    ]

    filtered = provider._filter_events(events, regions=[MacroRegion.US], days_ahead=7)

    assert [event.event_id for event in filtered] == ["e-1"]


def test_fetch_upcoming_events_sorts_by_scheduled_at_and_deduplicates_by_event_id() -> None:
    provider = FakeMacroCalendarProvider()
    now = datetime.now(timezone.utc)

    first = _build_event("dup", now + timedelta(days=4), MacroRegion.US)
    second = _build_event("dup", now + timedelta(days=2), MacroRegion.US)
    third = _build_event("other", now + timedelta(days=3), MacroRegion.US)

    ordered = provider._prepare_results([first, second, third])

    assert [event.event_id for event in ordered] == ["dup", "other"]
    assert [event.scheduled_at for event in ordered] == sorted(
        [event.scheduled_at for event in ordered],
        key=lambda value: value,
    )


def test_fetch_upcoming_events_returns_empty_list_when_no_events_match() -> None:
    provider = FakeMacroCalendarProvider()
    now = datetime.now(timezone.utc)

    events = [
        _build_event("e-1", now + timedelta(days=10), MacroRegion.US),
    ]

    filtered = provider._filter_events(events, regions=[MacroRegion.US], days_ahead=3)

    assert filtered == []
