from dataclasses import dataclass
from datetime import datetime, timezone

from application.opening_picture_observation_guard import (
    OpeningPictureObservationClassification,
    OpeningPictureObservationGuard,
)


@dataclass(frozen=True)
class Observation:
    observation_id: str
    event_time: datetime
    first_seen_at: datetime


TIME_ZERO = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)


def test_observation_before_time_zero_is_historical_material() -> None:
    observation = Observation(
        observation_id="old-filing",
        event_time=datetime(2026, 8, 25, 9, 59, tzinfo=timezone.utc),
        first_seen_at=datetime(2026, 8, 25, 10, 1, tzinfo=timezone.utc),
    )
    guard = OpeningPictureObservationGuard(time_zero=TIME_ZERO)

    result = guard.observe(
        observation_id=observation.observation_id,
        event_time=observation.event_time,
        first_seen_at=observation.first_seen_at,
        observation=observation,
    )

    assert (
        result.classification
        is OpeningPictureObservationClassification.HISTORICAL
    )
    assert result.retained_live_observation is None


def test_old_event_first_seen_after_time_zero_is_not_live() -> None:
    observation = Observation(
        observation_id="2017-event",
        event_time=datetime(2017, 4, 3, 12, 0, tzinfo=timezone.utc),
        first_seen_at=datetime(2026, 8, 25, 10, 3, tzinfo=timezone.utc),
    )
    guard = OpeningPictureObservationGuard(time_zero=TIME_ZERO)

    result = guard.observe(
        observation_id=observation.observation_id,
        event_time=observation.event_time,
        first_seen_at=observation.first_seen_at,
        observation=observation,
    )

    assert (
        result.classification
        is OpeningPictureObservationClassification.HISTORICAL
    )
    assert result.retained_live_observation is None


def test_post_time_zero_observation_is_retained_as_pending_live_work() -> None:
    observation = Observation(
        observation_id="new-filing",
        event_time=datetime(2026, 8, 25, 10, 2, tzinfo=timezone.utc),
        first_seen_at=datetime(2026, 8, 25, 10, 3, tzinfo=timezone.utc),
    )
    guard = OpeningPictureObservationGuard(time_zero=TIME_ZERO)

    result = guard.observe(
        observation_id=observation.observation_id,
        event_time=observation.event_time,
        first_seen_at=observation.first_seen_at,
        observation=observation,
    )

    assert (
        result.classification
        is OpeningPictureObservationClassification.PENDING_LIVE
    )
    assert result.retained_live_observation is not None
    assert result.retained_live_observation.observation is observation
