from datetime import datetime, timezone

import pytest

from application.opening_picture_lifecycle import OpeningPictureLifecycle
from application.opening_picture_observation_guard import (
    OpeningPictureObservationClassification,
    RetainedLiveObservation,
)
from models.holding_protection_epoch import HoldingProtectionEpoch
from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)
from models.opening_picture_state import OpeningPictureState


CANONICAL_ID = "verified-instrument:AAPL"
TIME_ZERO = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)
HISTORICAL_TIME = datetime(2017, 1, 3, 12, 0, tzinfo=timezone.utc)
LIVE_EVENT_TIME = datetime(2026, 8, 25, 10, 2, tzinfo=timezone.utc)
FIRST_SEEN_AT = datetime(2026, 8, 25, 10, 3, tzinfo=timezone.utc)
REQUIRED_MEMBERS = ("identity", "opening_context")


def new_lifecycle() -> OpeningPictureLifecycle:
    return OpeningPictureLifecycle.start(
        canonical_instrument_id=CANONICAL_ID,
        required_member_ids=REQUIRED_MEMBERS,
        clock=lambda: TIME_ZERO,
    )


def retained_live_observation() -> RetainedLiveObservation:
    return RetainedLiveObservation(
        observation_id="new-filing",
        event_time=LIVE_EVENT_TIME,
        first_seen_at=FIRST_SEEN_AT,
        observation={"source": "SEC", "title": "New filing"},
    )


def test_new_holding_begins_learning_with_stable_time_zero() -> None:
    lifecycle = new_lifecycle()

    assert lifecycle.is_ready is False
    assert lifecycle.state.protection_epoch.time_zero == TIME_ZERO

    lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )

    assert lifecycle.is_ready is False
    assert lifecycle.state.protection_epoch.time_zero == TIME_ZERO


@pytest.mark.parametrize(
    "blocking_status",
    (
        OpeningPictureMemberResultStatus.UNAVAILABLE,
        OpeningPictureMemberResultStatus.UNSUPPORTED,
        OpeningPictureMemberResultStatus.CONFLICT,
    ),
)
def test_unresolved_required_result_keeps_lifecycle_learning(
    blocking_status: OpeningPictureMemberResultStatus,
) -> None:
    lifecycle = new_lifecycle()
    lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )

    update = lifecycle.record_member_result(
        "opening_context",
        blocking_status,
    )

    assert lifecycle.is_ready is False
    assert update.became_ready is False
    assert update.released_observations == ()


@pytest.mark.parametrize(
    "satisfying_status",
    (
        OpeningPictureMemberResultStatus.ESTABLISHED,
        OpeningPictureMemberResultStatus.ESTABLISHED_ABSENCE,
        OpeningPictureMemberResultStatus.NOT_APPLICABLE,
    ),
)
def test_all_required_satisfying_results_transition_once_to_ready(
    satisfying_status: OpeningPictureMemberResultStatus,
) -> None:
    lifecycle = new_lifecycle()
    first = lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )

    transition = lifecycle.record_member_result(
        "opening_context",
        satisfying_status,
    )
    repeated = lifecycle.record_member_result(
        "opening_context",
        satisfying_status,
    )

    assert first.became_ready is False
    assert lifecycle.is_ready is True
    assert transition.became_ready is True
    assert repeated.became_ready is False


def test_live_observation_is_silent_during_learning_and_released_once_at_ready(
) -> None:
    lifecycle = new_lifecycle()

    observation_result = lifecycle.observe(
        observation_id="new-filing",
        event_time=LIVE_EVENT_TIME,
        first_seen_at=FIRST_SEEN_AT,
        observation={"source": "SEC", "title": "New filing"},
    )
    first_update = lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )
    ready_update = lifecycle.record_member_result(
        "opening_context",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )
    repeated_update = lifecycle.record_member_result(
        "opening_context",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )

    assert observation_result.classification is (
        OpeningPictureObservationClassification.PENDING_LIVE
    )
    assert first_update.released_observations == ()
    assert ready_update.released_observations == (
        {"source": "SEC", "title": "New filing"},
    )
    assert repeated_update.released_observations == ()


def test_historical_learning_material_is_never_released_as_live_work() -> None:
    lifecycle = new_lifecycle()

    historical_result = lifecycle.observe(
        observation_id="old-filing",
        event_time=HISTORICAL_TIME,
        first_seen_at=FIRST_SEEN_AT,
        observation={"source": "SEC", "title": "2017 filing"},
    )
    lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )
    ready_update = lifecycle.record_member_result(
        "opening_context",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )

    assert historical_result.classification is (
        OpeningPictureObservationClassification.HISTORICAL
    )
    assert ready_update.released_observations == ()


def test_restored_partial_state_resumes_learning_with_original_time_zero() -> None:
    restored_state = OpeningPictureState(
        contract_version=1,
        protection_epoch=HoldingProtectionEpoch(CANONICAL_ID, TIME_ZERO),
        required_member_ids=REQUIRED_MEMBERS,
        required_member_results={
            "identity": OpeningPictureMemberResultStatus.ESTABLISHED,
        },
        optional_member_results={},
        retained_live_observations=(retained_live_observation(),),
    )

    lifecycle = OpeningPictureLifecycle.restore(
        state=restored_state,
        required_member_ids=REQUIRED_MEMBERS,
    )

    assert lifecycle.is_ready is False
    assert lifecycle.state.protection_epoch.time_zero == TIME_ZERO
    assert lifecycle.state.retained_live_observations == (
        retained_live_observation(),
    )


def test_restored_ready_state_remains_ready_without_a_new_transition() -> None:
    restored_state = OpeningPictureState(
        contract_version=1,
        protection_epoch=HoldingProtectionEpoch(CANONICAL_ID, TIME_ZERO),
        required_member_ids=REQUIRED_MEMBERS,
        required_member_results={
            "identity": OpeningPictureMemberResultStatus.ESTABLISHED,
            "opening_context": (
                OpeningPictureMemberResultStatus.ESTABLISHED_ABSENCE
            ),
        },
        optional_member_results={},
        retained_live_observations=(),
    )

    lifecycle = OpeningPictureLifecycle.restore(
        state=restored_state,
        required_member_ids=REQUIRED_MEMBERS,
    )
    reevaluation = lifecycle.record_member_result(
        "opening_context",
        OpeningPictureMemberResultStatus.ESTABLISHED_ABSENCE,
    )

    assert lifecycle.is_ready is True
    assert lifecycle.state.protection_epoch.time_zero == TIME_ZERO
    assert reevaluation.became_ready is False
    assert reevaluation.released_observations == ()


def test_restored_ready_state_exposes_pending_for_delivery_without_clearing(
) -> None:
    retained = retained_live_observation()
    restored_state = OpeningPictureState(
        contract_version=1,
        protection_epoch=HoldingProtectionEpoch(CANONICAL_ID, TIME_ZERO),
        required_member_ids=REQUIRED_MEMBERS,
        required_member_results={
            "identity": OpeningPictureMemberResultStatus.ESTABLISHED,
            "opening_context": (
                OpeningPictureMemberResultStatus.ESTABLISHED_ABSENCE
            ),
        },
        optional_member_results={},
        retained_live_observations=(retained,),
    )

    lifecycle = OpeningPictureLifecycle.restore(
        state=restored_state,
        required_member_ids=REQUIRED_MEMBERS,
    )

    assert lifecycle.is_ready is True
    assert lifecycle.delivery_eligible_pending_observations() == (retained,)
    assert lifecycle.state.retained_live_observations == (retained,)
    assert lifecycle.delivery_eligible_pending_observations() == (retained,)
