from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from models.macro_event import MacroEvent


def get_upcoming_macro_events(
    events: Iterable[MacroEvent],
    *,
    now: datetime | None = None,
    look_ahead_days: int = 14,
) -> list[MacroEvent]:
    """Return macro events that are upcoming within the configured look-ahead window."""
    current_time = now or datetime.now(timezone.utc)
    if look_ahead_days < 0:
        raise ValueError("look_ahead_days must be non-negative")

    cutoff = current_time + timedelta(days=look_ahead_days)
    upcoming = [
        event
        for event in events
        if current_time <= event.scheduled_at <= cutoff
    ]

    return sorted(upcoming, key=lambda event: (event.scheduled_at, event.event_id))
