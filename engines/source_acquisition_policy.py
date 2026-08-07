from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class SourceAcquisitionPolicy:
    source_name: str
    interval_seconds: int
    publication_time: time | None = None
    publication_window_minutes: int | None = None
    publication_interval_seconds: int | None = None
    publication_timezone: str | None = None

    def __post_init__(self) -> None:
        if not self.source_name.strip():
            raise ValueError("source_name must not be empty")

        if self.interval_seconds < 1:
            raise ValueError("interval_seconds must be at least 1")

        publication_fields = (
            self.publication_time,
            self.publication_window_minutes,
            self.publication_interval_seconds,
        )

        configured_publication_fields = sum(
            value is not None
            for value in publication_fields
        )

        if configured_publication_fields not in (0, 3):
            raise ValueError(
                "publication configuration must be complete"
            )

        if (
            self.publication_window_minutes is not None
            and self.publication_window_minutes < 1
        ):
            raise ValueError(
                "publication_window_minutes must be at least 1"
            )

        if (
            self.publication_interval_seconds is not None
            and self.publication_interval_seconds < 1
        ):
            raise ValueError(
                "publication_interval_seconds must be at least 1"
            )

        if self.publication_timezone is not None:
            ZoneInfo(self.publication_timezone)

    def interval_at(self, current_time: time) -> int:
        if self.publication_time is None:
            return self.interval_seconds

        anchor = datetime.combine(
            datetime.today().date(),
            self.publication_time,
        )
        current = datetime.combine(
            anchor.date(),
            current_time,
        )

        window = timedelta(
            minutes=self.publication_window_minutes,
        )

        if anchor - window <= current <= anchor + window:
            return self.publication_interval_seconds

        return self.interval_seconds

    def interval_at_datetime(
        self,
        current_datetime: datetime,
    ) -> int:
        if self.publication_timezone is None:
            return self.interval_at(
                current_datetime.timetz().replace(tzinfo=None)
            )

        source_time = current_datetime.astimezone(
            ZoneInfo(self.publication_timezone)
        )

        return self.interval_at(
            source_time.timetz().replace(tzinfo=None)
        )
