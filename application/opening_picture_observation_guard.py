from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class OpeningPictureObservationClassification(str, Enum):
    HISTORICAL = "historical"
    PENDING_LIVE = "pending_live"


@dataclass(frozen=True, slots=True)
class RetainedLiveObservation:
    observation_id: str
    event_time: datetime
    first_seen_at: datetime
    observation: Any

    def __post_init__(self) -> None:
        if not isinstance(self.observation_id, str):
            raise TypeError("observation_id must be a string")
        normalized_observation_id = self.observation_id.strip()
        if not normalized_observation_id:
            raise ValueError("observation_id must not be empty")
        if (
            not isinstance(self.event_time, datetime)
            or self.event_time.tzinfo is None
            or self.event_time.utcoffset() is None
        ):
            raise ValueError("event_time must be timezone-aware")
        if (
            not isinstance(self.first_seen_at, datetime)
            or self.first_seen_at.tzinfo is None
            or self.first_seen_at.utcoffset() is None
        ):
            raise ValueError("first_seen_at must be timezone-aware")

        object.__setattr__(
            self,
            "observation_id",
            normalized_observation_id,
        )


@dataclass(frozen=True, slots=True)
class DeliveryAcknowledgement:
    retained_observation: RetainedLiveObservation
    acknowledged_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(
            self.retained_observation,
            RetainedLiveObservation,
        ):
            raise TypeError(
                "retained_observation must be a RetainedLiveObservation"
            )
        if (
            not isinstance(self.acknowledged_at, datetime)
            or self.acknowledged_at.tzinfo is None
            or self.acknowledged_at.utcoffset() is None
        ):
            raise ValueError("acknowledged_at must be timezone-aware")
        if self.acknowledged_at < self.retained_observation.first_seen_at:
            raise ValueError(
                "acknowledged_at must not precede first_seen_at"
            )


@dataclass(frozen=True, slots=True)
class OpeningPictureObservationResult:
    classification: OpeningPictureObservationClassification
    retained_live_observation: RetainedLiveObservation | None = None


class OpeningPictureObservationGuard:
    def __init__(
        self,
        *,
        time_zero: datetime,
        restored_pending: tuple[RetainedLiveObservation, ...] = (),
    ) -> None:
        self._validate_aware_datetime("time_zero", time_zero)
        self._time_zero = time_zero
        self._pending: dict[str, RetainedLiveObservation] = {}

        for retained in restored_pending:
            if not isinstance(retained, RetainedLiveObservation):
                raise TypeError(
                    "restored_pending must contain RetainedLiveObservation"
                )

            if retained.observation_id in self._pending:
                raise ValueError("duplicate restored observation_id")

            self._pending[retained.observation_id] = retained

    def observe(
        self,
        *,
        observation_id: str,
        event_time: datetime,
        first_seen_at: datetime,
        observation: Any,
    ) -> OpeningPictureObservationResult:
        normalized_observation_id = observation_id.strip()
        if not normalized_observation_id:
            raise ValueError("observation_id must not be empty")

        self._validate_aware_datetime("event_time", event_time)
        self._validate_aware_datetime("first_seen_at", first_seen_at)

        if event_time < self._time_zero:
            return OpeningPictureObservationResult(
                classification=(
                    OpeningPictureObservationClassification.HISTORICAL
                ),
            )

        if event_time == self._time_zero:
            raise ValueError(
                "event_time equal to time_zero has no approved classification"
            )

        retained = self._pending.get(normalized_observation_id)
        if retained is None:
            retained = RetainedLiveObservation(
                observation_id=normalized_observation_id,
                event_time=event_time,
                first_seen_at=first_seen_at,
                observation=observation,
            )
            self._pending[normalized_observation_id] = retained

        return OpeningPictureObservationResult(
            classification=(
                OpeningPictureObservationClassification.PENDING_LIVE
            ),
            retained_live_observation=retained,
        )

    def remove_pending(
        self,
        *,
        observation_id: str,
    ) -> RetainedLiveObservation | None:
        if not isinstance(observation_id, str):
            raise TypeError("observation_id must be a string")
        normalized_observation_id = observation_id.strip()
        if not normalized_observation_id:
            raise ValueError("observation_id must not be empty")

        return self._pending.pop(normalized_observation_id, None)

    def release_pending(
        self,
        *,
        is_ready: bool,
    ) -> tuple[Any, ...]:
        if not is_ready:
            return ()

        observations = tuple(
            retained.observation
            for retained in self._pending.values()
        )
        self._pending.clear()

        return observations

    @staticmethod
    def _validate_aware_datetime(
        field_name: str,
        value: datetime,
    ) -> None:
        if (
            not isinstance(value, datetime)
            or value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(f"{field_name} must be timezone-aware")
