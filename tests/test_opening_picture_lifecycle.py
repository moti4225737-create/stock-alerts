from dataclasses import fields, is_dataclass
from datetime import datetime, timedelta, timezone

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
PROGRESS_AT = datetime(2026, 8, 25, 10, 4, tzinfo=timezone.utc)
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


def test_control_exposes_when_meaningful_learning_progress_occurred() -> None:
    clock_values = iter((TIME_ZERO, PROGRESS_AT))
    lifecycle = OpeningPictureLifecycle.start(
        canonical_instrument_id=CANONICAL_ID,
        required_member_ids=REQUIRED_MEMBERS,
        clock=lambda: next(clock_values),
    )

    lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )

    assert lifecycle.is_ready is False
    snapshot = lifecycle.control_snapshot()
    datetime_evidence = {
        getattr(snapshot, field.name)
        for field in fields(snapshot)
        if isinstance(getattr(snapshot, field.name), datetime)
    }
    assert PROGRESS_AT in datetime_evidence

    snapshot_after_progress = snapshot
    lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )

    assert lifecycle.control_snapshot() == snapshot_after_progress


def test_control_reports_learning_no_progress_beyond_supplied_duration() -> None:
    allowed_no_progress = timedelta(minutes=5)
    evaluated_at = PROGRESS_AT + timedelta(minutes=10)
    clock_values = iter((TIME_ZERO, PROGRESS_AT))
    lifecycle = OpeningPictureLifecycle.start(
        canonical_instrument_id=CANONICAL_ID,
        required_member_ids=REQUIRED_MEMBERS,
        clock=lambda: next(clock_values),
    )
    lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )
    state_before_control = lifecycle.state

    snapshot = lifecycle.control_snapshot()
    evaluate_no_progress = getattr(
        snapshot,
        "evaluate_no_progress",
        None,
    )

    assert callable(evaluate_no_progress), (
        "Opening Picture control lacks read-only no-progress evaluation"
    )
    control_exception = evaluate_no_progress(
        evaluated_at=evaluated_at,
        allowed_no_progress=allowed_no_progress,
    )
    assert control_exception is not None
    assert is_dataclass(control_exception)
    evidence = {
        getattr(control_exception, field.name)
        for field in fields(control_exception)
    }
    assert CANONICAL_ID in evidence
    assert PROGRESS_AT in evidence
    assert evaluated_at in evidence
    assert allowed_no_progress in evidence
    assert evaluated_at - PROGRESS_AT in evidence
    assert any(
        isinstance(value, str)
        and "no-progress" in value.lower().replace("_", "-")
        for value in evidence
    )
    assert lifecycle.state == state_before_control
    assert lifecycle.is_ready is False


def test_control_reports_ready_pending_work_beyond_supplied_duration() -> None:
    allowed_pending = timedelta(minutes=5)
    evaluated_at = FIRST_SEEN_AT + timedelta(minutes=10)
    lifecycle = new_lifecycle()
    observation_result = lifecycle.observe(
        observation_id="new-filing",
        event_time=LIVE_EVENT_TIME,
        first_seen_at=FIRST_SEEN_AT,
        observation={"source": "SEC", "title": "New filing"},
    )
    retained = observation_result.retained_live_observation
    assert retained is not None
    lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )
    lifecycle.record_member_result(
        "opening_context",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )
    assert lifecycle.is_ready is True
    state_before_control = lifecycle.state
    pending_before_control = lifecycle.delivery_eligible_pending_observations()

    snapshot = lifecycle.control_snapshot()
    evaluate_pending_delivery = getattr(
        snapshot,
        "evaluate_pending_delivery",
        None,
    )

    assert callable(evaluate_pending_delivery), (
        "Opening Picture control lacks read-only READY pending-age evaluation"
    )
    control_exception = evaluate_pending_delivery(
        evaluated_at=evaluated_at,
        allowed_pending=allowed_pending,
    )
    assert control_exception is not None
    assert is_dataclass(control_exception)
    evidence = {
        getattr(control_exception, field.name)
        for field in fields(control_exception)
    }
    assert CANONICAL_ID in evidence
    assert FIRST_SEEN_AT in evidence
    assert evaluated_at in evidence
    assert allowed_pending in evidence
    assert evaluated_at - FIRST_SEEN_AT in evidence
    assert any(
        isinstance(value, str)
        and "pending" in value.lower()
        and "overdue" in value.lower()
        for value in evidence
    )
    assert lifecycle.state == state_before_control
    assert lifecycle.delivery_eligible_pending_observations() == (
        pending_before_control
    )
    assert lifecycle.state.delivery_acknowledgements == ()


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


def test_becoming_ready_keeps_observation_pending_and_delivery_eligible(
) -> None:
    lifecycle = new_lifecycle()
    assert lifecycle.is_ready is False

    observation_result = lifecycle.observe(
        observation_id="new-filing",
        event_time=LIVE_EVENT_TIME,
        first_seen_at=FIRST_SEEN_AT,
        observation={"source": "SEC", "title": "New filing"},
    )
    retained_observation = observation_result.retained_live_observation
    assert retained_observation is not None

    lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )
    ready_update = lifecycle.record_member_result(
        "opening_context",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )

    assert observation_result.classification is (
        OpeningPictureObservationClassification.PENDING_LIVE
    )
    assert ready_update.became_ready is True
    assert lifecycle.state.retained_live_observations == (
        retained_observation,
    )
    assert lifecycle.delivery_eligible_pending_observations() == (
        retained_observation,
    )

    second_delivery_read = (
        lifecycle.delivery_eligible_pending_observations()
    )

    assert second_delivery_read == (retained_observation,)
    assert lifecycle.state.retained_live_observations == (
        retained_observation,
    )


def test_acknowledgement_moves_only_one_pending_observation_to_control_evidence(
) -> None:
    lifecycle = new_lifecycle()
    assert lifecycle.is_ready is False

    first_result = lifecycle.observe(
        observation_id="first-filing",
        event_time=LIVE_EVENT_TIME,
        first_seen_at=FIRST_SEEN_AT,
        observation={"source": "SEC", "title": "First filing"},
    )
    second_result = lifecycle.observe(
        observation_id="second-filing",
        event_time=datetime(
            2026,
            8,
            25,
            10,
            4,
            tzinfo=timezone.utc,
        ),
        first_seen_at=datetime(
            2026,
            8,
            25,
            10,
            5,
            tzinfo=timezone.utc,
        ),
        observation={"source": "SEC", "title": "Second filing"},
    )
    first_retained = first_result.retained_live_observation
    second_retained = second_result.retained_live_observation
    assert first_retained is not None
    assert second_retained is not None

    lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )
    lifecycle.record_member_result(
        "opening_context",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )

    assert lifecycle.is_ready is True
    assert lifecycle.delivery_eligible_pending_observations() == (
        first_retained,
        second_retained,
    )

    acknowledged_at = datetime(
        2026,
        8,
        25,
        10,
        10,
        tzinfo=timezone.utc,
    )
    acknowledged = lifecycle.acknowledge_delivery(
        observation_id=first_retained.observation_id,
        acknowledged_at=acknowledged_at,
    )

    assert acknowledged is True
    assert lifecycle.state.retained_live_observations == (second_retained,)
    assert lifecycle.delivery_eligible_pending_observations() == (
        second_retained,
    )
    assert len(lifecycle.state.delivery_acknowledgements) == 1
    acknowledgement = lifecycle.state.delivery_acknowledgements[0]
    assert acknowledgement.retained_observation == first_retained
    assert acknowledgement.acknowledged_at == acknowledged_at

    repeated = lifecycle.acknowledge_delivery(
        observation_id=first_retained.observation_id,
        acknowledged_at=datetime(
            2026,
            8,
            25,
            10,
            11,
            tzinfo=timezone.utc,
        ),
    )

    assert repeated is False
    assert lifecycle.state.delivery_acknowledgements == (acknowledgement,)
    assert acknowledgement.acknowledged_at == acknowledged_at
    assert lifecycle.state.retained_live_observations == (second_retained,)
    assert lifecycle.delivery_eligible_pending_observations() == (
        second_retained,
    )


def test_control_snapshot_reports_lifecycle_state_without_mutation() -> None:
    lifecycle = new_lifecycle()
    assert lifecycle.is_ready is False

    first_result = lifecycle.observe(
        observation_id="first-filing",
        event_time=LIVE_EVENT_TIME,
        first_seen_at=FIRST_SEEN_AT,
        observation={"source": "SEC", "title": "First filing"},
    )
    remaining_first_seen_at = datetime(
        2026,
        8,
        25,
        10,
        5,
        tzinfo=timezone.utc,
    )
    second_result = lifecycle.observe(
        observation_id="second-filing",
        event_time=datetime(
            2026,
            8,
            25,
            10,
            4,
            tzinfo=timezone.utc,
        ),
        first_seen_at=remaining_first_seen_at,
        observation={"source": "SEC", "title": "Second filing"},
    )
    first_retained = first_result.retained_live_observation
    second_retained = second_result.retained_live_observation
    assert first_retained is not None
    assert second_retained is not None

    lifecycle.record_member_result(
        "identity",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )
    lifecycle.record_member_result(
        "opening_context",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )
    assert lifecycle.is_ready is True

    acknowledged_at = datetime(
        2026,
        8,
        25,
        10,
        10,
        tzinfo=timezone.utc,
    )
    assert lifecycle.acknowledge_delivery(
        observation_id=first_retained.observation_id,
        acknowledged_at=acknowledged_at,
    ) is True
    state_before_query = lifecycle.state

    first_snapshot = lifecycle.control_snapshot()

    assert first_snapshot.canonical_instrument_id == CANONICAL_ID
    assert first_snapshot.time_zero == TIME_ZERO
    assert first_snapshot.contract_version == 1
    assert first_snapshot.is_ready is True
    assert first_snapshot.pending_count == 1
    assert (
        first_snapshot.oldest_pending_first_seen_at
        == remaining_first_seen_at
    )
    assert first_snapshot.acknowledgement_count == 1
    assert first_snapshot.last_acknowledged_at == acknowledged_at

    second_snapshot = lifecycle.control_snapshot()

    assert second_snapshot == first_snapshot
    assert lifecycle.state == state_before_query
    assert lifecycle.is_ready is True
    assert lifecycle.delivery_eligible_pending_observations() == (
        second_retained,
    )


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
    lifecycle.record_member_result(
        "opening_context",
        OpeningPictureMemberResultStatus.ESTABLISHED,
    )

    assert historical_result.classification is (
        OpeningPictureObservationClassification.HISTORICAL
    )


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
        clock=lambda: TIME_ZERO,
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
        clock=lambda: TIME_ZERO,
    )
    reevaluation = lifecycle.record_member_result(
        "opening_context",
        OpeningPictureMemberResultStatus.ESTABLISHED_ABSENCE,
    )

    assert lifecycle.is_ready is True
    assert lifecycle.state.protection_epoch.time_zero == TIME_ZERO
    assert reevaluation.became_ready is False


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
        clock=lambda: TIME_ZERO,
    )

    assert lifecycle.is_ready is True
    assert lifecycle.delivery_eligible_pending_observations() == (retained,)
    assert lifecycle.state.retained_live_observations == (retained,)
    assert lifecycle.delivery_eligible_pending_observations() == (retained,)
