from datetime import datetime, timedelta, timezone
from decimal import Decimal

from engines.upcoming_macro_events import get_upcoming_macro_events
from models.macro_event import MacroEvent, MacroEventStatus, MacroEventType
from models.macro_region import MacroRegion


def build_macro_event(**overrides: object) -> MacroEvent:
    defaults = {
        "event_id": "event-001",
        "event_type": MacroEventType.CPI,
        "name": "Consumer Price Index",
        "country": MacroRegion.US,
        "scheduled_at": datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc),
        "status": MacroEventStatus.SCHEDULED,
        "actual": Decimal("3.2"),
        "forecast": Decimal("3.1"),
        "previous": Decimal("3.0"),
        "unit": "%",
        "source": "FRED",
    }
    defaults.update(overrides)
    return MacroEvent(**defaults)


def test_past_events_are_ignored_and_today_events_are_included() -> None:
    now = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)
    past_event = build_macro_event(event_id="past", scheduled_at=now - timedelta(hours=1))
    today_event = build_macro_event(event_id="today", scheduled_at=now + timedelta(hours=3))
    future_event = build_macro_event(event_id="future", scheduled_at=now + timedelta(days=2))

    result = get_upcoming_macro_events([past_event, today_event, future_event], now=now)

    assert [event.event_id for event in result] == ["today", "future"]


def test_events_are_returned_chronologically() -> None:
    now = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)
    first = build_macro_event(event_id="later", scheduled_at=now + timedelta(days=2))
    second = build_macro_event(event_id="earlier", scheduled_at=now + timedelta(days=1))

    result = get_upcoming_macro_events([first, second], now=now)

    assert [event.event_id for event in result] == ["earlier", "later"]


def test_default_look_ahead_window_filters_events_outside_14_days() -> None:
    now = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)
    inside = build_macro_event(event_id="inside", scheduled_at=now + timedelta(days=14))
    outside = build_macro_event(event_id="outside", scheduled_at=now + timedelta(days=15))

    result = get_upcoming_macro_events([inside, outside], now=now)

    assert [event.event_id for event in result] == ["inside"]


def test_custom_look_ahead_window_can_be_configured() -> None:
    now = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)
    inside = build_macro_event(event_id="inside", scheduled_at=now + timedelta(days=7))
    outside = build_macro_event(event_id="outside", scheduled_at=now + timedelta(days=8))

    result = get_upcoming_macro_events([inside, outside], now=now, look_ahead_days=7)

    assert [event.event_id for event in result] == ["inside"]


def test_empty_input_returns_empty_output() -> None:
    result = get_upcoming_macro_events([], now=datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc))

    assert result == []


def test_behavior_is_deterministic_for_same_inputs_in_different_orders() -> None:
    now = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)
    first = build_macro_event(event_id="beta", scheduled_at=now + timedelta(days=2))
    second = build_macro_event(event_id="alpha", scheduled_at=now + timedelta(days=1))

    result_a = get_upcoming_macro_events([first, second], now=now)
    result_b = get_upcoming_macro_events([second, first], now=now)

    assert [event.event_id for event in result_a] == ["alpha", "beta"]
    assert [event.event_id for event in result_b] == ["alpha", "beta"]
