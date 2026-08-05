import re

from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult


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
            return (
                "\u05d4\u05e0\u05d9\u05e1\u05d5\u05d9 "
                "\u05d4\u05e7\u05dc\u05d9\u05e0\u05d9 "
                "\u05d4\u05d5\u05e9\u05dc\u05dd."
            )

        if status == "RECRUITING":
            return (
                "\u05d4\u05e0\u05d9\u05e1\u05d5\u05d9 "
                "\u05d4\u05e7\u05dc\u05d9\u05e0\u05d9 "
                "\u05e0\u05de\u05e6\u05d0 "
                "\u05db\u05e2\u05ea "
                "\u05d1\u05e1\u05d8\u05d8\u05d5\u05e1 Recruiting."
            )

        return (
            "\u05e4\u05d5\u05e8\u05e1\u05dd "
            "\u05e2\u05d3\u05db\u05d5\u05df "
            "\u05dc\u05e1\u05d8\u05d8\u05d5\u05e1 "
            "\u05d4\u05e0\u05d9\u05e1\u05d5\u05d9 "
            "\u05d4\u05e7\u05dc\u05d9\u05e0\u05d9: "
            f"{status.title().replace('_', ' ')}."
        )

    def build_result(self, event: Event) -> InvestorRuleResult:
        return InvestorRuleResult(
            summary=self.build_summary(event),
            explanation=Explanation(
                why_it_matters=(
                    "\u05e9\u05d9\u05e0\u05d5\u05d9 "
                    "\u05d1\u05e1\u05d8\u05d8\u05d5\u05e1 "
                    "\u05e0\u05d9\u05e1\u05d5\u05d9 "
                    "\u05e7\u05dc\u05d9\u05e0\u05d9 "
                    "\u05e2\u05e9\u05d5\u05d9 "
                    "\u05dc\u05e9\u05e0\u05d5\u05ea "
                    "\u05d0\u05ea "
                    "\u05d4\u05d4\u05e2\u05e8\u05db\u05d4 "
                    "\u05dc\u05d2\u05d1\u05d9 "
                    "\u05d4\u05e1\u05d9\u05db\u05d5\u05d9 "
                    "\u05dc\u05d4\u05e6\u05dc\u05d7\u05d4 "
                    "\u05d5\u05dc\u05d0\u05d9\u05e9\u05d5\u05e8 "
                    "\u05e2\u05ea\u05d9\u05d3\u05d9."
                ),
                market_context=(
                    "\u05d9\u05e9 "
                    "\u05dc\u05d1\u05d3\u05d5\u05e7 "
                    "\u05d0\u05ea "
                    "\u05d4\u05e1\u05d9\u05d1\u05d4 "
                    "\u05dc\u05e9\u05d9\u05e0\u05d5\u05d9 "
                    "\u05d4\u05e1\u05d8\u05d8\u05d5\u05e1, "
                    "\u05d0\u05ea "
                    "\u05d4\u05e9\u05dc\u05d1 "
                    "\u05d4\u05e7\u05dc\u05d9\u05e0\u05d9 "
                    "\u05d5\u05d0\u05ea "
                    "\u05d4\u05e2\u05d3\u05db\u05d5\u05e0\u05d9\u05dd "
                    "\u05d4\u05d1\u05d0\u05d9\u05dd "
                    "\u05e9\u05e6\u05e4\u05d5\u05d9\u05d9\u05dd "
                    "\u05de\u05d4\u05d7\u05d1\u05e8\u05d4."
                ),
            ),
        )

    def _extract_status(self, summary: str) -> str | None:
        match = self._STATUS_PATTERN.search(summary)

        if match is None:
            return None

        return match.group(1).upper()
