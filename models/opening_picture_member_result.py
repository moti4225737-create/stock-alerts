from enum import Enum


class OpeningPictureMemberResultStatus(str, Enum):
    ESTABLISHED = "established"
    ESTABLISHED_ABSENCE = "established_absence"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    CONFLICT = "conflict"
    NOT_APPLICABLE = "not_applicable"
