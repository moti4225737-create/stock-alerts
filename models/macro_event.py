from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Mapping

from models.macro_event_status import MacroEventStatus
from models.macro_event_type import MacroEventType
from models.macro_region import MacroRegion
from models.macro_surprise_direction import MacroSurpriseDirection


@dataclass(frozen=True, slots=True)
class MacroEvent:
    event_id: str
    event_type: MacroEventType
    name: str
    country: MacroRegion
    scheduled_at: datetime
    status: MacroEventStatus
    actual: Decimal | None
    forecast: Decimal | None
    previous: Decimal | None
    unit: str | None
    source: str
    source_url: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._validate_required_string("event_id", self.event_id)
        self._validate_required_string("name", self.name)
        self._validate_required_string("source", self.source)
        self._validate_required_string("country", self.country.value if isinstance(self.country, MacroRegion) else str(self.country))

        if not isinstance(self.scheduled_at, datetime):
            raise TypeError("scheduled_at must be a datetime")

        if self.scheduled_at.tzinfo is None:
            raise ValueError("scheduled_at must be timezone-aware")

        if not isinstance(self.actual, Decimal) and self.actual is not None:
            raise TypeError("actual must be a Decimal or None")

        if not isinstance(self.forecast, Decimal) and self.forecast is not None:
            raise TypeError("forecast must be a Decimal or None")

        if not isinstance(self.previous, Decimal) and self.previous is not None:
            raise TypeError("previous must be a Decimal or None")

        if not isinstance(self.event_type, MacroEventType):
            raise TypeError("event_type must be a MacroEventType")

        if not isinstance(self.status, MacroEventStatus):
            raise TypeError("status must be a MacroEventStatus")

        if not isinstance(self.country, MacroRegion):
            raise TypeError("country must be a MacroRegion")

        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def surprise_direction(self) -> MacroSurpriseDirection:
        if self.actual is None or self.forecast is None:
            return MacroSurpriseDirection.UNKNOWN

        if self.actual > self.forecast:
            return MacroSurpriseDirection.ABOVE_FORECAST

        if self.actual < self.forecast:
            return MacroSurpriseDirection.BELOW_FORECAST

        return MacroSurpriseDirection.IN_LINE

    @property
    def surprise_value(self) -> Decimal | None:
        if self.actual is None or self.forecast is None:
            return None

        return self.actual - self.forecast

    @staticmethod
    def _validate_required_string(field_name: str, value: str | None) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must not be empty")
