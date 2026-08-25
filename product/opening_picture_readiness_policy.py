from collections.abc import Iterable

from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)


class OpeningPictureReadinessPolicy:
    _SATISFYING_STATUSES = {
        OpeningPictureMemberResultStatus.ESTABLISHED,
        OpeningPictureMemberResultStatus.ESTABLISHED_ABSENCE,
        OpeningPictureMemberResultStatus.NOT_APPLICABLE,
    }

    def is_ready(
        self,
        *,
        required_statuses: Iterable[OpeningPictureMemberResultStatus],
        optional_statuses: Iterable[
            OpeningPictureMemberResultStatus
        ] = (),
    ) -> bool:
        del optional_statuses

        return all(
            status in self._SATISFYING_STATUSES
            for status in required_statuses
        )
