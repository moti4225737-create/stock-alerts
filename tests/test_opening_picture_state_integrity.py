from datetime import datetime, timezone

import pytest

from application.opening_picture_observation_guard import (
    DeliveryAcknowledgement,
    RetainedLiveObservation,
)
from models.holding_protection_epoch import HoldingProtectionEpoch
from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)
from models.opening_picture_state import OpeningPictureState


CANONICAL_ID = "verified-instrument:AAPL"
TIME_ZERO = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)
EVENT_TIME = datetime(2026, 8, 25, 10, 2, tzinfo=timezone.utc)
FIRST_SEEN_AT = datetime(2026, 8, 25, 10, 3, tzinfo=timezone.utc)
ACKNOWLEDGED_AT = datetime(2026, 8, 25, 10, 4, tzinfo=timezone.utc)
REQUIRED_MEMBER_ID = "time_zero"


def retained_observation(
    observation_id: str = "new-filing",
    *,
    event_time: datetime = EVENT_TIME,
    first_seen_at: datetime = FIRST_SEEN_AT,
) -> RetainedLiveObservation:
    return RetainedLiveObservation(
        observation_id=observation_id,
        event_time=event_time,
        first_seen_at=first_seen_at,
        observation={"source": "SEC", "title": "New filing"},
    )


def opening_picture_state(
    *,
    pending: tuple[RetainedLiveObservation, ...] = (),
    acknowledgements: tuple[DeliveryAcknowledgement, ...] = (),
) -> OpeningPictureState:
    return OpeningPictureState(
        contract_version=1,
        protection_epoch=HoldingProtectionEpoch(
            canonical_instrument_id=CANONICAL_ID,
            time_zero=TIME_ZERO,
        ),
        required_member_ids=(REQUIRED_MEMBER_ID,),
        required_member_results={
            REQUIRED_MEMBER_ID: (
                OpeningPictureMemberResultStatus.ESTABLISHED
            ),
        },
        optional_member_results={},
        retained_live_observations=pending,
        delivery_acknowledgements=acknowledgements,
    )


def test_retained_observation_normalizes_observation_id() -> None:
    retained = retained_observation("  new-filing  ")

    assert retained.observation_id == "new-filing"


def test_retained_observation_rejects_empty_observation_id() -> None:
    with pytest.raises(
        ValueError,
        match="^observation_id must not be empty$",
    ):
        retained_observation("   ")


@pytest.mark.parametrize(
    ("field_name", "event_time", "first_seen_at"),
    (
        (
            "event_time",
            datetime(2026, 8, 25, 10, 2),
            FIRST_SEEN_AT,
        ),
        (
            "first_seen_at",
            EVENT_TIME,
            datetime(2026, 8, 25, 10, 3),
        ),
    ),
)
def test_retained_observation_rejects_timezone_naive_timestamps(
    field_name: str,
    event_time: datetime,
    first_seen_at: datetime,
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"^{field_name} must be timezone-aware$",
    ):
        retained_observation(
            event_time=event_time,
            first_seen_at=first_seen_at,
        )


def test_state_rejects_duplicate_normalized_pending_ids() -> None:
    with pytest.raises(
        ValueError,
        match="^duplicate pending observation_id$",
    ):
        opening_picture_state(
            pending=(
                retained_observation("new-filing"),
                retained_observation("  new-filing  "),
            ),
        )


def test_state_rejects_duplicate_normalized_acknowledgement_ids() -> None:
    first = DeliveryAcknowledgement(
        retained_observation=retained_observation("new-filing"),
        acknowledged_at=ACKNOWLEDGED_AT,
    )
    second = DeliveryAcknowledgement(
        retained_observation=retained_observation("  new-filing  "),
        acknowledged_at=ACKNOWLEDGED_AT,
    )

    with pytest.raises(
        ValueError,
        match="^duplicate acknowledged observation_id$",
    ):
        opening_picture_state(acknowledgements=(first, second))


def test_state_rejects_pending_and_acknowledged_id_overlap() -> None:
    pending = retained_observation("new-filing")
    acknowledgement = DeliveryAcknowledgement(
        retained_observation=retained_observation("  new-filing  "),
        acknowledged_at=ACKNOWLEDGED_AT,
    )

    with pytest.raises(
        ValueError,
        match=(
            "^observation_id cannot be both pending and acknowledged$"
        ),
    ):
        opening_picture_state(
            pending=(pending,),
            acknowledgements=(acknowledgement,),
        )


def test_acknowledgement_rejects_timestamp_before_first_seen_at() -> None:
    with pytest.raises(
        ValueError,
        match="^acknowledged_at must not precede first_seen_at$",
    ):
        DeliveryAcknowledgement(
            retained_observation=retained_observation(),
            acknowledged_at=datetime(
                2026,
                8,
                25,
                10,
                2,
                tzinfo=timezone.utc,
            ),
        )


def test_acknowledgement_allows_timestamp_equal_to_first_seen_at() -> None:
    retained = retained_observation()

    acknowledgement = DeliveryAcknowledgement(
        retained_observation=retained,
        acknowledged_at=retained.first_seen_at,
    )

    assert acknowledgement.acknowledged_at == retained.first_seen_at
