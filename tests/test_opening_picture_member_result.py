from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)


def test_opening_picture_member_result_statuses_are_distinct() -> None:
    assert {
        status.name: status.value
        for status in OpeningPictureMemberResultStatus
    } == {
        "ESTABLISHED": "established",
        "ESTABLISHED_ABSENCE": "established_absence",
        "UNAVAILABLE": "unavailable",
        "UNSUPPORTED": "unsupported",
        "CONFLICT": "conflict",
        "NOT_APPLICABLE": "not_applicable",
    }

    assert (
        OpeningPictureMemberResultStatus.ESTABLISHED_ABSENCE
        is not OpeningPictureMemberResultStatus.UNAVAILABLE
    )
    assert (
        OpeningPictureMemberResultStatus.NOT_APPLICABLE
        is not OpeningPictureMemberResultStatus.UNSUPPORTED
    )
