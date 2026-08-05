import re

from models.event import Event


class ClinicalTrialStatusSummaryRule:
    rule_id = "clinical_trials.status"
    priority = 300

    _STATUS_PATTERN = re.compile(
        r"(?:^|\|\s*)Status:\s*([A-Z_]+)",
        re.IGNORECASE,
    )

    def matches(self, event: Event) -> bool:
        return (
            event.source.upper() == "CLINICALTRIALS.GOV"
            and self._extract_status(event.summary) is not None
        )

    def build_summary(self, event: Event) -> str:
        status = self._extract_status(event.summary)

        if status == "COMPLETED":
            return "הניסוי הקליני הושלם."

        if status == "RECRUITING":
            return "הניסוי הקליני נמצא כעת בסטטוס Recruiting."

        return (
            "פורסם עדכון לסטטוס הניסוי הקליני: "
            f"{status.title().replace('_', ' ')}."
        )

    def _extract_status(self, summary: str) -> str | None:
        match = self._STATUS_PATTERN.search(summary)

        if match is None:
            return None

        return match.group(1).upper()
