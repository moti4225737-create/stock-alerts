from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from models.macro_event import MacroEvent
from models.macro_event_status import MacroEventStatus
from models.macro_region import MacroRegion


class MacroCalendarProvider(ABC):
    """Minimal interface for macro calendar providers."""

    @abstractmethod
    def fetch_upcoming_events(
        self,
        *,
        regions: list[MacroRegion] | None = None,
        days_ahead: int = 30,
    ) -> list[MacroEvent]:
        raise NotImplementedError

    def _filter_events(
        self,
        events: list[MacroEvent],
        *,
        regions: list[MacroRegion] | None = None,
        days_ahead: int = 30,
    ) -> list[MacroEvent]:
        now = datetime.now(timezone.utc)
        window_end = now + timedelta(days=days_ahead + (3 if days_ahead >= 7 else 0))
        requested_regions = set(regions or [])

        matching_events: list[MacroEvent] = []
        for event in events:
            if event.status is MacroEventStatus.CANCELLED:
                continue
            if requested_regions and event.country not in requested_regions:
                continue
            if event.scheduled_at < now:
                continue
            if event.scheduled_at > window_end:
                continue
            matching_events.append(event)

        return matching_events

    def _prepare_results(self, events: list[MacroEvent]) -> list[MacroEvent]:
        ordered_events = sorted(events, key=lambda event: event.scheduled_at)
        seen_event_ids: set[str] = set()
        prepared_events: list[MacroEvent] = []

        for event in ordered_events:
            if event.event_id in seen_event_ids:
                continue
            seen_event_ids.add(event.event_id)
            prepared_events.append(event)

        return prepared_events
