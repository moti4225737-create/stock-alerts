from datetime import datetime, timezone
from dataclasses import dataclass

from models.event import Event


@dataclass(frozen=True, slots=True)
class IntelligenceTimeline:
    """
    Chronological intelligence for a single company symbol.

    IntelligenceTimeline is derived from Events and represents the
    temporal history of intelligence associated with a company.
    """

    symbol: str
    events: tuple[Event, ...] = ()

    def __post_init__(self) -> None:
        normalized_symbol = self.symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError("symbol must not be empty")

        ordered_events = tuple(
            sorted(
                self.events,
                key=lambda event: self._sort_key(event),
            )
        )

        object.__setattr__(self, "symbol", normalized_symbol)
        object.__setattr__(self, "events", ordered_events)

    @property
    def latest_event(self) -> Event | None:
        if not self.events:
            return None

        return self.events[-1]

    @staticmethod
    def _sort_key(event: Event) -> tuple[datetime, str]:
        published_at = event.published_at

        if not isinstance(published_at, str) or not published_at.strip():
            raise ValueError(
                "Event.published_at must be a non-empty ISO-8601 date or datetime string"
            )

        try:
            parsed_value = datetime.fromisoformat(
                published_at.replace("Z", "+00:00")
            )
        except ValueError as error:
            raise ValueError(
                "Event.published_at must be a non-empty ISO-8601 date or datetime string"
            ) from error

        if parsed_value.tzinfo is None:
            parsed_value = parsed_value.replace(tzinfo=timezone.utc)
        else:
            parsed_value = parsed_value.astimezone(timezone.utc)

        return parsed_value, event.title or ""
