from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from application.opening_picture_observation_guard import (
    DeliveryAcknowledgement,
    OpeningPictureObservationGuard,
    OpeningPictureObservationResult,
    RetainedLiveObservation,
)
from models.holding_protection_epoch import HoldingProtectionEpochs
from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)
from models.opening_picture_state import OpeningPictureState
from product.opening_picture_readiness_policy import (
    OpeningPictureReadinessPolicy,
)


@dataclass(frozen=True, slots=True)
class OpeningPictureLifecycleUpdate:
    became_ready: bool


@dataclass(frozen=True, slots=True)
class OpeningPictureControlException:
    canonical_instrument_id: str
    reason: str
    evaluated_at: datetime
    evidence_at: datetime
    allowed_duration: timedelta
    elapsed_duration: timedelta


@dataclass(frozen=True, slots=True)
class OpeningPictureControlSnapshot:
    canonical_instrument_id: str
    time_zero: datetime
    contract_version: int
    is_ready: bool
    pending_count: int
    oldest_pending_first_seen_at: datetime | None
    acknowledgement_count: int
    last_acknowledged_at: datetime | None
    last_meaningful_learning_progress_at: datetime | None

    def evaluate_no_progress(
        self,
        *,
        evaluated_at: datetime,
        allowed_no_progress: timedelta,
    ) -> OpeningPictureControlException | None:
        progress_at = self.last_meaningful_learning_progress_at
        if self.is_ready or progress_at is None:
            return None

        elapsed_no_progress = evaluated_at - progress_at
        if elapsed_no_progress <= allowed_no_progress:
            return None

        return OpeningPictureControlException(
            canonical_instrument_id=self.canonical_instrument_id,
            reason="learning_no_progress",
            evaluated_at=evaluated_at,
            evidence_at=progress_at,
            allowed_duration=allowed_no_progress,
            elapsed_duration=elapsed_no_progress,
        )

    def evaluate_pending_delivery(
        self,
        *,
        evaluated_at: datetime,
        allowed_pending: timedelta,
    ) -> OpeningPictureControlException | None:
        oldest_pending_at = self.oldest_pending_first_seen_at
        if (
            not self.is_ready
            or self.pending_count == 0
            or oldest_pending_at is None
        ):
            return None

        elapsed_pending = evaluated_at - oldest_pending_at
        if elapsed_pending <= allowed_pending:
            return None

        return OpeningPictureControlException(
            canonical_instrument_id=self.canonical_instrument_id,
            reason="ready_pending_overdue",
            evaluated_at=evaluated_at,
            evidence_at=oldest_pending_at,
            allowed_duration=allowed_pending,
            elapsed_duration=elapsed_pending,
        )


class OpeningPictureLifecycle:
    def __init__(
        self,
        *,
        state: OpeningPictureState,
        required_member_ids: Iterable[str],
        clock: Callable[[], datetime],
    ) -> None:
        self._clock = clock
        self._required_member_ids = self._validated_member_ids(
            required_member_ids
        )
        self._state = OpeningPictureState(
            contract_version=state.contract_version,
            protection_epoch=state.protection_epoch,
            required_member_results=state.required_member_results,
            optional_member_results=state.optional_member_results,
            retained_live_observations=state.retained_live_observations,
            delivery_acknowledgements=state.delivery_acknowledgements,
            last_meaningful_learning_progress_at=(
                state.last_meaningful_learning_progress_at
            ),
            required_member_ids=self._required_member_ids,
        )
        self._observation_guard = OpeningPictureObservationGuard(
            time_zero=self._state.protection_epoch.time_zero,
        )
        self._is_ready = self._derive_readiness(self._state)

    @classmethod
    def start(
        cls,
        *,
        canonical_instrument_id: str,
        required_member_ids: Iterable[str],
        clock: Callable[[], datetime],
    ) -> "OpeningPictureLifecycle":
        required_member_ids = tuple(required_member_ids)
        protection_epoch = HoldingProtectionEpochs(clock=clock).establish(
            canonical_instrument_id
        )
        return cls(
            state=OpeningPictureState(
                contract_version=1,
                protection_epoch=protection_epoch,
                required_member_results={},
                optional_member_results={},
                retained_live_observations=(),
                required_member_ids=required_member_ids,
            ),
            required_member_ids=required_member_ids,
            clock=clock,
        )

    @classmethod
    def restore(
        cls,
        *,
        state: OpeningPictureState,
        required_member_ids: Iterable[str],
        clock: Callable[[], datetime],
    ) -> "OpeningPictureLifecycle":
        return cls(
            state=state,
            required_member_ids=required_member_ids,
            clock=clock,
        )

    @property
    def state(self) -> OpeningPictureState:
        return self._state

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def delivery_eligible_pending_observations(
        self,
    ) -> tuple[RetainedLiveObservation, ...]:
        if not self._is_ready:
            return ()

        return self._state.retained_live_observations

    def control_snapshot(self) -> OpeningPictureControlSnapshot:
        return OpeningPictureControlSnapshot(
            canonical_instrument_id=(
                self._state.protection_epoch.canonical_instrument_id
            ),
            time_zero=self._state.protection_epoch.time_zero,
            contract_version=self._state.contract_version,
            is_ready=self._is_ready,
            pending_count=len(self._state.retained_live_observations),
            oldest_pending_first_seen_at=min(
                (
                    retained.first_seen_at
                    for retained in self._state.retained_live_observations
                ),
                default=None,
            ),
            acknowledgement_count=len(
                self._state.delivery_acknowledgements
            ),
            last_acknowledged_at=max(
                (
                    acknowledgement.acknowledged_at
                    for acknowledgement in (
                        self._state.delivery_acknowledgements
                    )
                ),
                default=None,
            ),
            last_meaningful_learning_progress_at=(
                self._state.last_meaningful_learning_progress_at
            ),
        )

    def acknowledge_delivery(
        self,
        *,
        observation_id: str,
        acknowledged_at: datetime,
    ) -> bool:
        if not self._is_ready:
            raise RuntimeError(
                "delivery acknowledgement requires a READY lifecycle"
            )
        self._validate_aware_datetime("acknowledged_at", acknowledged_at)

        if not isinstance(observation_id, str):
            raise TypeError("observation_id must be a string")
        normalized_observation_id = observation_id.strip()
        if not normalized_observation_id:
            raise ValueError("observation_id must not be empty")

        retained = next(
            (
                pending
                for pending in self._state.retained_live_observations
                if pending.observation_id == normalized_observation_id
            ),
            None,
        )
        if retained is None:
            return False

        acknowledgement = DeliveryAcknowledgement(
            retained_observation=retained,
            acknowledged_at=acknowledged_at,
        )
        self._state = self._with_state(
            retained_live_observations=tuple(
                pending
                for pending in self._state.retained_live_observations
                if pending.observation_id != retained.observation_id
            ),
            delivery_acknowledgements=(
                *self._state.delivery_acknowledgements,
                acknowledgement,
            ),
        )
        return True

    def record_member_result(
        self,
        member_id: str,
        status: OpeningPictureMemberResultStatus,
    ) -> OpeningPictureLifecycleUpdate:
        if not isinstance(member_id, str):
            raise TypeError("member_id must be a string")
        normalized_member_id = member_id.strip()
        if normalized_member_id not in self._required_member_ids:
            raise ValueError("member_id is not a required lifecycle member")
        if not isinstance(status, OpeningPictureMemberResultStatus):
            raise TypeError(
                "status must be an OpeningPictureMemberResultStatus"
            )

        previous_status = self._state.required_member_results.get(
            normalized_member_id
        )
        made_meaningful_progress = (
            not self._status_satisfies_readiness(previous_status)
            and self._status_satisfies_readiness(status)
        )
        required_results = dict(self._state.required_member_results)
        required_results[normalized_member_id] = status
        updated_state = self._with_state(
            required_member_results=required_results,
            last_meaningful_learning_progress_at=(
                self._clock()
                if made_meaningful_progress
                else self._state.last_meaningful_learning_progress_at
            ),
        )
        updated_is_ready = self._derive_readiness(updated_state)
        became_ready = not self._is_ready and updated_is_ready

        self._state = updated_state
        self._is_ready = updated_is_ready

        return OpeningPictureLifecycleUpdate(
            became_ready=became_ready,
        )

    def observe(
        self,
        *,
        observation_id: str,
        event_time: datetime,
        first_seen_at: datetime,
        observation: Any,
    ) -> OpeningPictureObservationResult:
        if self._is_ready:
            raise RuntimeError(
                "READY observations belong to normal Sentinel processing"
            )

        result = self._observation_guard.observe(
            observation_id=observation_id,
            event_time=event_time,
            first_seen_at=first_seen_at,
            observation=observation,
        )
        retained = result.retained_live_observation
        if retained is not None:
            existing = next(
                (
                    pending
                    for pending in self._state.retained_live_observations
                    if pending.observation_id == retained.observation_id
                ),
                None,
            )
            if existing is not None:
                return OpeningPictureObservationResult(
                    classification=result.classification,
                    retained_live_observation=existing,
                )

            self._state = self._with_state(
                retained_live_observations=(
                    *self._state.retained_live_observations,
                    retained,
                ),
            )

        return result

    def _derive_readiness(self, state: OpeningPictureState) -> bool:
        recorded_member_ids = set(state.required_member_results)
        return (
            self._required_member_ids <= recorded_member_ids
            and state.is_ready
        )

    def _with_state(
        self,
        *,
        state: OpeningPictureState | None = None,
        required_member_results: dict[
            str,
            OpeningPictureMemberResultStatus,
        ]
        | None = None,
        retained_live_observations: (
            tuple[RetainedLiveObservation, ...] | None
        ) = None,
        delivery_acknowledgements: (
            tuple[DeliveryAcknowledgement, ...] | None
        ) = None,
        last_meaningful_learning_progress_at: datetime | None = None,
    ) -> OpeningPictureState:
        current = state or self._state
        return OpeningPictureState(
            contract_version=current.contract_version,
            protection_epoch=current.protection_epoch,
            required_member_results=(
                current.required_member_results
                if required_member_results is None
                else required_member_results
            ),
            optional_member_results=current.optional_member_results,
            retained_live_observations=(
                current.retained_live_observations
                if retained_live_observations is None
                else retained_live_observations
            ),
            delivery_acknowledgements=(
                current.delivery_acknowledgements
                if delivery_acknowledgements is None
                else delivery_acknowledgements
            ),
            last_meaningful_learning_progress_at=(
                current.last_meaningful_learning_progress_at
                if last_meaningful_learning_progress_at is None
                else last_meaningful_learning_progress_at
            ),
            required_member_ids=current.required_member_ids,
        )

    @staticmethod
    def _status_satisfies_readiness(
        status: OpeningPictureMemberResultStatus | None,
    ) -> bool:
        return status is not None and OpeningPictureReadinessPolicy().is_ready(
            required_statuses=(status,),
        )

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

    @staticmethod
    def _validated_member_ids(
        member_ids: Iterable[str],
    ) -> frozenset[str]:
        normalized: list[str] = []
        for member_id in member_ids:
            if not isinstance(member_id, str) or not member_id.strip():
                raise ValueError("required member identity must not be empty")
            normalized.append(member_id.strip())

        if len(normalized) != len(set(normalized)):
            raise ValueError("duplicate required member identity")
        if not normalized:
            raise ValueError("at least one required member is needed")

        return frozenset(normalized)
