from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Iterable, Mapping

from application.opening_picture_observation_guard import (
    DeliveryAcknowledgement,
    RetainedLiveObservation,
)
from models.holding_protection_epoch import HoldingProtectionEpoch
from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)
from product.opening_picture_readiness_policy import (
    OpeningPictureReadinessPolicy,
)


@dataclass(frozen=True, slots=True)
class OpeningPictureState:
    contract_version: int
    protection_epoch: HoldingProtectionEpoch
    required_member_ids: Iterable[str]
    required_member_results: Mapping[
        str,
        OpeningPictureMemberResultStatus,
    ]
    optional_member_results: Mapping[
        str,
        OpeningPictureMemberResultStatus,
    ]
    retained_live_observations: tuple[RetainedLiveObservation, ...]
    delivery_acknowledgements: tuple[DeliveryAcknowledgement, ...] = ()
    last_meaningful_learning_progress_at: datetime | None = None

    def __post_init__(self) -> None:
        if isinstance(self.contract_version, bool) or not isinstance(
            self.contract_version,
            int,
        ):
            raise TypeError("contract_version must be an integer")

        if not isinstance(self.protection_epoch, HoldingProtectionEpoch):
            raise TypeError(
                "protection_epoch must be a HoldingProtectionEpoch"
            )

        required = self._validated_member_results(
            "required_member_results",
            self.required_member_results,
        )
        optional = self._validated_member_results(
            "optional_member_results",
            self.optional_member_results,
        )
        required_member_ids = self._validated_required_member_ids(
            self.required_member_ids
        )

        if not required_member_ids:
            raise ValueError("required formula must not be empty")

        if not required.keys() <= required_member_ids:
            raise ValueError(
                "required member result is not part of the required formula"
            )

        if required.keys() & optional.keys():
            raise ValueError(
                "a member cannot be both required and optional"
            )

        retained = tuple(self.retained_live_observations)
        if not all(
            isinstance(observation, RetainedLiveObservation)
            for observation in retained
        ):
            raise TypeError(
                "retained_live_observations must contain "
                "RetainedLiveObservation"
            )

        acknowledgements = tuple(self.delivery_acknowledgements)
        if not all(
            isinstance(acknowledgement, DeliveryAcknowledgement)
            for acknowledgement in acknowledgements
        ):
            raise TypeError(
                "delivery_acknowledgements must contain "
                "DeliveryAcknowledgement"
            )

        progress_at = self.last_meaningful_learning_progress_at
        if progress_at is not None and (
            not isinstance(progress_at, datetime)
            or progress_at.tzinfo is None
            or progress_at.utcoffset() is None
        ):
            raise ValueError(
                "last_meaningful_learning_progress_at must be timezone-aware"
            )
        if (
            progress_at is not None
            and progress_at < self.protection_epoch.time_zero
        ):
            raise ValueError(
                "last_meaningful_learning_progress_at must not precede "
                "time_zero"
            )

        pending_ids = [
            observation.observation_id
            for observation in retained
        ]
        if len(pending_ids) != len(set(pending_ids)):
            raise ValueError("duplicate pending observation_id")

        acknowledged_ids = [
            acknowledgement.retained_observation.observation_id
            for acknowledgement in acknowledgements
        ]
        if len(acknowledged_ids) != len(set(acknowledged_ids)):
            raise ValueError("duplicate acknowledged observation_id")

        if set(pending_ids) & set(acknowledged_ids):
            raise ValueError(
                "observation_id cannot be both pending and acknowledged"
            )

        object.__setattr__(
            self,
            "required_member_results",
            MappingProxyType(required),
        )
        object.__setattr__(
            self,
            "optional_member_results",
            MappingProxyType(optional),
        )
        object.__setattr__(
            self,
            "retained_live_observations",
            retained,
        )
        object.__setattr__(
            self,
            "delivery_acknowledgements",
            acknowledgements,
        )
        object.__setattr__(
            self,
            "required_member_ids",
            required_member_ids,
        )

    @property
    def is_ready(self) -> bool:
        if not self.required_member_ids <= self.required_member_results.keys():
            return False

        return OpeningPictureReadinessPolicy().is_ready(
            required_statuses=(
                self.required_member_results[member_id]
                for member_id in self.required_member_ids
            ),
            optional_statuses=self.optional_member_results.values(),
        )

    @staticmethod
    def _validated_required_member_ids(
        member_ids: Iterable[str],
    ) -> frozenset[str]:
        normalized: list[str] = []
        for member_id in member_ids:
            if not isinstance(member_id, str) or not member_id.strip():
                raise ValueError("required member identity must not be empty")
            normalized.append(member_id.strip())

        if len(normalized) != len(set(normalized)):
            raise ValueError("duplicate required member identity")

        return frozenset(normalized)

    @staticmethod
    def _validated_member_results(
        field_name: str,
        member_results: Mapping[str, OpeningPictureMemberResultStatus],
    ) -> dict[str, OpeningPictureMemberResultStatus]:
        if not isinstance(member_results, Mapping):
            raise TypeError(f"{field_name} must be a mapping")

        validated: dict[str, OpeningPictureMemberResultStatus] = {}
        for member_id, status in member_results.items():
            if not isinstance(member_id, str) or not member_id.strip():
                raise ValueError("member identity must not be empty")
            if not isinstance(status, OpeningPictureMemberResultStatus):
                raise TypeError(
                    "member result must be an "
                    "OpeningPictureMemberResultStatus"
                )
            validated[member_id.strip()] = status

        return validated
