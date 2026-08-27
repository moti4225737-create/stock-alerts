import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from application.opening_picture_observation_guard import (
    DeliveryAcknowledgement,
    RetainedLiveObservation,
)
from models.holding_protection_epoch import HoldingProtectionEpoch
from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)
from models.opening_picture_state import OpeningPictureState


class OpeningPictureStorageError(RuntimeError):
    pass


class FileOpeningPictureStore:
    CONTRACT_VERSION = 1

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def load(
        self,
        canonical_instrument_id: str,
    ) -> OpeningPictureState | None:
        try:
            states = self._read_states()
            if states is None:
                return None
            return states.get(canonical_instrument_id)
        except (
            OSError,
            UnicodeError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as exc:
            raise OpeningPictureStorageError(
                "Unable to load Opening Picture state"
            ) from exc

    def save(self, state: OpeningPictureState) -> None:
        temporary_path: Path | None = None

        try:
            if not isinstance(state, OpeningPictureState):
                raise TypeError("state must be an OpeningPictureState")
            if state.contract_version != self.CONTRACT_VERSION:
                raise ValueError("unsupported Opening Picture contract version")

            states = self._read_states() or {}
            states[state.protection_epoch.canonical_instrument_id] = state
            serialized = json.dumps(
                self._serialize_states(states),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            self._path.parent.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(serialized)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, self._path)
            temporary_path = None
        except (
            OSError,
            UnicodeError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as exc:
            raise OpeningPictureStorageError(
                "Unable to save Opening Picture state"
            ) from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def _read_states(self) -> dict[str, OpeningPictureState] | None:
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        return self._deserialize_states(payload)

    @classmethod
    def _serialize_states(
        cls,
        states: dict[str, OpeningPictureState],
    ) -> dict:
        return {
            "contract_version": cls.CONTRACT_VERSION,
            "holdings": {
                canonical_id: cls._serialize_state(state)
                for canonical_id, state in states.items()
            },
        }

    @staticmethod
    def _serialize_state(state: OpeningPictureState) -> dict:
        return {
            "time_zero": state.protection_epoch.time_zero.isoformat(),
            "required_member_ids": sorted(state.required_member_ids),
            "required_member_results": {
                member_id: status.value
                for member_id, status in (
                    state.required_member_results.items()
                )
            },
            "optional_member_results": {
                member_id: status.value
                for member_id, status in (
                    state.optional_member_results.items()
                )
            },
            "retained_live_observations": [
                {
                    "observation_id": retained.observation_id,
                    "event_time": retained.event_time.isoformat(),
                    "first_seen_at": retained.first_seen_at.isoformat(),
                    "observation": retained.observation,
                }
                for retained in state.retained_live_observations
            ],
            "delivery_acknowledgements": [
                {
                    "retained_observation": {
                        "observation_id": (
                            acknowledgement
                            .retained_observation
                            .observation_id
                        ),
                        "event_time": (
                            acknowledgement
                            .retained_observation
                            .event_time
                            .isoformat()
                        ),
                        "first_seen_at": (
                            acknowledgement
                            .retained_observation
                            .first_seen_at
                            .isoformat()
                        ),
                        "observation": (
                            acknowledgement.retained_observation.observation
                        ),
                    },
                    "acknowledged_at": (
                        acknowledgement.acknowledged_at.isoformat()
                    ),
                }
                for acknowledgement in state.delivery_acknowledgements
            ],
        }

    @classmethod
    def _deserialize_states(
        cls,
        payload: object,
    ) -> dict[str, OpeningPictureState]:
        if not isinstance(payload, dict):
            raise ValueError("persisted Opening Picture must be an object")
        if payload["contract_version"] != cls.CONTRACT_VERSION:
            raise ValueError("unsupported Opening Picture contract version")

        holdings = payload["holdings"]
        if not isinstance(holdings, dict):
            raise ValueError("holdings must be an object")

        return {
            canonical_id: cls._deserialize_state(canonical_id, state_payload)
            for canonical_id, state_payload in holdings.items()
        }

    @classmethod
    def _deserialize_state(
        cls,
        canonical_id: object,
        payload: object,
    ) -> OpeningPictureState:
        if not isinstance(canonical_id, str) or not canonical_id.strip():
            raise ValueError("canonical holding identity must not be empty")
        if not isinstance(payload, dict):
            raise ValueError("holding state must be an object")

        retained_payload = payload["retained_live_observations"]
        if not isinstance(retained_payload, list):
            raise ValueError("retained_live_observations must be an array")
        acknowledgement_payload = payload["delivery_acknowledgements"]
        if not isinstance(acknowledgement_payload, list):
            raise ValueError("delivery_acknowledgements must be an array")

        return OpeningPictureState(
            contract_version=cls.CONTRACT_VERSION,
            protection_epoch=HoldingProtectionEpoch(
                canonical_instrument_id=canonical_id,
                time_zero=cls._parse_datetime(payload["time_zero"]),
            ),
            required_member_ids=cls._deserialize_required_member_ids(
                payload["required_member_ids"]
            ),
            required_member_results=cls._deserialize_member_results(
                payload["required_member_results"]
            ),
            optional_member_results=cls._deserialize_member_results(
                payload["optional_member_results"]
            ),
            retained_live_observations=tuple(
                cls._deserialize_retained_observation(retained)
                for retained in retained_payload
            ),
            delivery_acknowledgements=tuple(
                cls._deserialize_delivery_acknowledgement(acknowledgement)
                for acknowledgement in acknowledgement_payload
            ),
        )

    @staticmethod
    def _deserialize_required_member_ids(
        payload: object,
    ) -> tuple[str, ...]:
        if not isinstance(payload, list):
            raise ValueError("required_member_ids must be an array")
        if not all(isinstance(member_id, str) for member_id in payload):
            raise ValueError("required_member_ids must contain strings")
        return tuple(payload)

    @staticmethod
    def _deserialize_member_results(
        payload: object,
    ) -> dict[str, OpeningPictureMemberResultStatus]:
        if not isinstance(payload, dict):
            raise ValueError("member results must be an object")
        return {
            member_id: OpeningPictureMemberResultStatus(status)
            for member_id, status in payload.items()
        }

    @classmethod
    def _deserialize_retained_observation(
        cls,
        payload: object,
    ) -> RetainedLiveObservation:
        if not isinstance(payload, dict):
            raise ValueError("retained observation must be an object")
        observation_id = payload["observation_id"]
        if not isinstance(observation_id, str) or not observation_id.strip():
            raise ValueError("observation_id must not be empty")

        event_time = cls._parse_datetime(payload["event_time"])
        first_seen_at = cls._parse_datetime(payload["first_seen_at"])
        cls._require_aware_datetime("event_time", event_time)
        cls._require_aware_datetime("first_seen_at", first_seen_at)

        return RetainedLiveObservation(
            observation_id=observation_id,
            event_time=event_time,
            first_seen_at=first_seen_at,
            observation=payload["observation"],
        )

    @classmethod
    def _deserialize_delivery_acknowledgement(
        cls,
        payload: object,
    ) -> DeliveryAcknowledgement:
        if not isinstance(payload, dict):
            raise ValueError("delivery acknowledgement must be an object")

        acknowledged_at = cls._parse_datetime(payload["acknowledged_at"])
        cls._require_aware_datetime("acknowledged_at", acknowledged_at)

        return DeliveryAcknowledgement(
            retained_observation=cls._deserialize_retained_observation(
                payload["retained_observation"]
            ),
            acknowledged_at=acknowledged_at,
        )

    @staticmethod
    def _parse_datetime(value: object) -> datetime:
        if not isinstance(value, str):
            raise ValueError("timestamp must be an ISO-8601 string")
        return datetime.fromisoformat(value)

    @staticmethod
    def _require_aware_datetime(field_name: str, value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware")
