from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
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


@dataclass(frozen=True, slots=True)
class OpeningPictureLifecycleUpdate:
    became_ready: bool
    released_observations: tuple[Any, ...] = ()


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


class OpeningPictureLifecycle:
    def __init__(
        self,
        *,
        state: OpeningPictureState,
        required_member_ids: Iterable[str],
    ) -> None:
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
            required_member_ids=self._required_member_ids,
        )
        self._observation_guard = OpeningPictureObservationGuard(
            time_zero=self._state.protection_epoch.time_zero,
            restored_pending=self._state.retained_live_observations,
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
        )

    @classmethod
    def restore(
        cls,
        *,
        state: OpeningPictureState,
        required_member_ids: Iterable[str],
    ) -> "OpeningPictureLifecycle":
        return cls(
            state=state,
            required_member_ids=required_member_ids,
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

        retained = self._observation_guard.remove_pending(
            observation_id=observation_id,
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

        required_results = dict(self._state.required_member_results)
        required_results[normalized_member_id] = status
        updated_state = self._with_state(
            required_member_results=required_results,
        )
        updated_is_ready = self._derive_readiness(updated_state)
        became_ready = not self._is_ready and updated_is_ready

        released_observations: tuple[Any, ...] = ()

        self._state = updated_state
        self._is_ready = updated_is_ready

        return OpeningPictureLifecycleUpdate(
            became_ready=became_ready,
            released_observations=released_observations,
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
        if retained is not None and all(
            existing.observation_id != retained.observation_id
            for existing in self._state.retained_live_observations
        ):
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
            required_member_ids=current.required_member_ids,
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
