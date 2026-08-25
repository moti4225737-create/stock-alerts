import json
from datetime import datetime, timezone

import pytest

from application.opening_picture_observation_guard import (
    OpeningPictureObservationGuard,
    RetainedLiveObservation,
)
from models.holding_protection_epoch import HoldingProtectionEpoch
from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)
from models.opening_picture_state import OpeningPictureState
from modules.file_opening_picture_store import (
    FileOpeningPictureStore,
    OpeningPictureStorageError,
)


CANONICAL_ID = "verified-instrument:AAPL"
TIME_ZERO = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)
EVENT_TIME = datetime(2026, 8, 25, 10, 2, tzinfo=timezone.utc)
FIRST_SEEN_AT = datetime(2026, 8, 25, 10, 3, tzinfo=timezone.utc)
REQUIRED_MEMBER_IDS = frozenset({"time_zero", "market_compass"})


def retained_observation() -> RetainedLiveObservation:
    return RetainedLiveObservation(
        observation_id="new-filing",
        event_time=EVENT_TIME,
        first_seen_at=FIRST_SEEN_AT,
        observation={"source": "SEC", "title": "New filing"},
    )


def partial_state() -> OpeningPictureState:
    return OpeningPictureState(
        contract_version=1,
        protection_epoch=HoldingProtectionEpoch(
            canonical_instrument_id=CANONICAL_ID,
            time_zero=TIME_ZERO,
        ),
        required_member_ids=REQUIRED_MEMBER_IDS,
        required_member_results={
            "time_zero": OpeningPictureMemberResultStatus.ESTABLISHED,
            "market_compass": OpeningPictureMemberResultStatus.UNAVAILABLE,
        },
        optional_member_results={},
        retained_live_observations=(retained_observation(),),
    )


def ready_state() -> OpeningPictureState:
    return OpeningPictureState(
        contract_version=1,
        protection_epoch=HoldingProtectionEpoch(
            canonical_instrument_id=CANONICAL_ID,
            time_zero=TIME_ZERO,
        ),
        required_member_ids=REQUIRED_MEMBER_IDS,
        required_member_results={
            "time_zero": OpeningPictureMemberResultStatus.ESTABLISHED,
            "market_compass": OpeningPictureMemberResultStatus.ESTABLISHED,
        },
        optional_member_results={},
        retained_live_observations=(retained_observation(),),
    )


def test_partial_opening_picture_restores_epoch_and_member_results(
    tmp_path,
) -> None:
    store = FileOpeningPictureStore(tmp_path / "opening_picture.json")
    original = partial_state()

    store.save(original)
    restored = store.load(CANONICAL_ID)

    assert restored is not None
    assert restored.protection_epoch == original.protection_epoch
    assert restored.required_member_results["time_zero"] is (
        OpeningPictureMemberResultStatus.ESTABLISHED
    )
    assert restored.required_member_results["market_compass"] is (
        OpeningPictureMemberResultStatus.UNAVAILABLE
    )
    assert restored.is_ready is False


def test_retained_live_observation_restores_without_early_release(
    tmp_path,
) -> None:
    store = FileOpeningPictureStore(tmp_path / "opening_picture.json")
    store.save(partial_state())

    restored = store.load(CANONICAL_ID)
    assert restored is not None
    assert restored.retained_live_observations == (retained_observation(),)

    guard = OpeningPictureObservationGuard(
        time_zero=restored.protection_epoch.time_zero,
        restored_pending=restored.retained_live_observations,
    )

    assert guard.release_pending(is_ready=restored.is_ready) == ()


def test_restored_pending_observation_can_release_after_state_is_ready(
    tmp_path,
) -> None:
    store = FileOpeningPictureStore(tmp_path / "opening_picture.json")
    store.save(partial_state())
    restored = store.load(CANONICAL_ID)
    assert restored is not None

    completed = ready_state()
    guard = OpeningPictureObservationGuard(
        time_zero=restored.protection_epoch.time_zero,
        restored_pending=restored.retained_live_observations,
    )

    assert completed.is_ready is True
    assert guard.release_pending(is_ready=completed.is_ready) == (
        retained_observation().observation,
    )
    assert guard.release_pending(is_ready=completed.is_ready) == ()


def test_previously_ready_opening_picture_restores_as_ready(tmp_path) -> None:
    store = FileOpeningPictureStore(tmp_path / "opening_picture.json")
    original = ready_state()

    store.save(original)
    restored = store.load(CANONICAL_ID)

    assert restored is not None
    assert restored.is_ready is True


def test_missing_state_is_distinct_from_partial_state(tmp_path) -> None:
    store = FileOpeningPictureStore(tmp_path / "opening_picture.json")

    assert store.load(CANONICAL_ID) is None

    store.save(partial_state())

    restored = store.load(CANONICAL_ID)
    assert restored is not None
    assert restored.is_ready is False


@pytest.mark.parametrize(
    "stored_payload",
    (
        "not valid json",
        json.dumps(
            {
                "contract_version": 999,
                "holdings": {},
            }
        ),
    ),
)
def test_malformed_or_incompatible_state_fails_closed(
    tmp_path,
    stored_payload: str,
) -> None:
    path = tmp_path / "opening_picture.json"
    path.write_text(stored_payload, encoding="utf-8")
    store = FileOpeningPictureStore(path)

    with pytest.raises(OpeningPictureStorageError):
        store.load(CANONICAL_ID)
