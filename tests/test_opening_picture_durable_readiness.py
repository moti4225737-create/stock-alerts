from datetime import datetime, timezone

import pytest

from models.holding_protection_epoch import HoldingProtectionEpoch
from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)
from models.opening_picture_state import OpeningPictureState
from modules.file_opening_picture_store import FileOpeningPictureStore


CANONICAL_ID = "verified-instrument:AAPL"
TIME_ZERO = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)
REQUIRED_MEMBER_IDS = frozenset(
    {
        "time_zero",
        "holding_identity",
        "market_compass",
    }
)


def opening_picture_state(
    required_member_results: dict[
        str,
        OpeningPictureMemberResultStatus,
    ],
) -> OpeningPictureState:
    return OpeningPictureState(
        contract_version=1,
        protection_epoch=HoldingProtectionEpoch(
            canonical_instrument_id=CANONICAL_ID,
            time_zero=TIME_ZERO,
        ),
        required_member_ids=REQUIRED_MEMBER_IDS,
        required_member_results=required_member_results,
        optional_member_results={},
        retained_live_observations=(),
    )


def test_required_member_ids_must_be_supplied() -> None:
    with pytest.raises(TypeError):
        OpeningPictureState(
            contract_version=1,
            protection_epoch=HoldingProtectionEpoch(
                canonical_instrument_id=CANONICAL_ID,
                time_zero=TIME_ZERO,
            ),
            required_member_results={},
            optional_member_results={},
            retained_live_observations=(),
        )


def test_required_formula_cannot_be_empty() -> None:
    with pytest.raises(
        ValueError,
        match="required formula must not be empty",
    ):
        OpeningPictureState(
            contract_version=1,
            protection_epoch=HoldingProtectionEpoch(
                canonical_instrument_id=CANONICAL_ID,
                time_zero=TIME_ZERO,
            ),
            required_member_ids=frozenset(),
            required_member_results={},
            optional_member_results={},
            retained_live_observations=(),
        )


def test_empty_or_partial_results_cannot_satisfy_durable_formula() -> None:
    empty = opening_picture_state(required_member_results={})
    partial = opening_picture_state(
        required_member_results={
            "time_zero": (
                OpeningPictureMemberResultStatus.ESTABLISHED
            ),
            "holding_identity": (
                OpeningPictureMemberResultStatus.ESTABLISHED
            ),
        }
    )

    assert empty.is_ready is False
    assert partial.is_ready is False


def test_complete_required_formula_can_become_ready() -> None:
    complete = opening_picture_state(
        required_member_results={
            member_id: OpeningPictureMemberResultStatus.ESTABLISHED
            for member_id in REQUIRED_MEMBER_IDS
        }
    )

    assert complete.is_ready is True


def test_required_formula_survives_store_and_restart(tmp_path) -> None:
    store = FileOpeningPictureStore(tmp_path / "opening_picture.json")
    original = opening_picture_state(
        required_member_results={
            "time_zero": (
                OpeningPictureMemberResultStatus.ESTABLISHED
            ),
        }
    )

    store.save(original)
    restored = store.load(CANONICAL_ID)

    assert restored is not None
    assert restored.required_member_ids == REQUIRED_MEMBER_IDS
    assert restored.required_member_results == {
        "time_zero": OpeningPictureMemberResultStatus.ESTABLISHED,
    }
    assert restored.is_ready is False
