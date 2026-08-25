import pytest

from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)
from product.opening_picture_readiness_policy import (
    OpeningPictureReadinessPolicy,
)


def test_all_required_members_established_is_ready() -> None:
    result = OpeningPictureReadinessPolicy().is_ready(
        required_statuses=(
            OpeningPictureMemberResultStatus.ESTABLISHED,
            OpeningPictureMemberResultStatus.ESTABLISHED,
        ),
    )

    assert result is True


@pytest.mark.parametrize(
    "blocking_status",
    (
        OpeningPictureMemberResultStatus.UNAVAILABLE,
        OpeningPictureMemberResultStatus.UNSUPPORTED,
        OpeningPictureMemberResultStatus.CONFLICT,
    ),
)
def test_unresolved_required_member_is_not_ready(
    blocking_status: OpeningPictureMemberResultStatus,
) -> None:
    result = OpeningPictureReadinessPolicy().is_ready(
        required_statuses=(
            OpeningPictureMemberResultStatus.ESTABLISHED,
            blocking_status,
        ),
    )

    assert result is False


def test_not_applicable_required_slot_does_not_block_ready() -> None:
    result = OpeningPictureReadinessPolicy().is_ready(
        required_statuses=(
            OpeningPictureMemberResultStatus.ESTABLISHED,
            OpeningPictureMemberResultStatus.NOT_APPLICABLE,
        ),
    )

    assert result is True


def test_established_absence_can_satisfy_required_member() -> None:
    result = OpeningPictureReadinessPolicy().is_ready(
        required_statuses=(
            OpeningPictureMemberResultStatus.ESTABLISHED,
            OpeningPictureMemberResultStatus.ESTABLISHED_ABSENCE,
        ),
    )

    assert result is True


def test_unavailable_optional_member_does_not_block_ready() -> None:
    result = OpeningPictureReadinessPolicy().is_ready(
        required_statuses=(
            OpeningPictureMemberResultStatus.ESTABLISHED,
        ),
        optional_statuses=(
            OpeningPictureMemberResultStatus.UNAVAILABLE,
        ),
    )

    assert result is True


def test_readiness_result_is_boolean_not_partial_state() -> None:
    ready = OpeningPictureReadinessPolicy().is_ready(
        required_statuses=(
            OpeningPictureMemberResultStatus.ESTABLISHED,
        ),
    )
    not_ready = OpeningPictureReadinessPolicy().is_ready(
        required_statuses=(
            OpeningPictureMemberResultStatus.UNAVAILABLE,
        ),
    )

    assert ready is True
    assert not_ready is False
