from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult


class SecLeadershipChangeSummaryRule:
    rule_id = "sec.8k.leadership_change"
    priority = 300

    _PATTERNS = (
        "DEPARTURE OF DIRECTORS OR CERTAIN OFFICERS",
        "APPOINTMENT OF CERTAIN OFFICERS",
        "ELECTION OF DIRECTORS",
    )

    def matches(self, event: Event) -> bool:
        raw_summary = event.summary.upper()

        return (
            event.source.upper() == "SEC"
            and "8-K" in event.title.upper()
            and any(
                pattern in raw_summary
                for pattern in self._PATTERNS
            )
        )

    def build_summary(self, event: Event) -> str:
        return (
            "\u05d4\u05d7\u05d1\u05e8\u05d4 "
            "\u05d3\u05d9\u05d5\u05d5\u05d7\u05d4 "
            "\u05e2\u05dc "
            "\u05e9\u05d9\u05e0\u05d5\u05d9 "
            "\u05d1\u05d4\u05e0\u05d4\u05dc\u05d4 "
            "\u05d0\u05d5 "
            "\u05d1\u05d3\u05d9\u05e8\u05e7\u05d8\u05d5\u05e8\u05d9\u05d5\u05df."
        )

    def build_result(self, event: Event) -> InvestorRuleResult:
        return InvestorRuleResult(
            summary=self.build_summary(event),
            explanation=Explanation(
                why_it_matters=(
                    "\u05e9\u05d9\u05e0\u05d5\u05d9 "
                    "\u05d1\u05d4\u05e0\u05d4\u05dc\u05d4 "
                    "\u05e2\u05e9\u05d5\u05d9 "
                    "\u05dc\u05d4\u05e9\u05e4\u05d9\u05e2 "
                    "\u05e2\u05dc "
                    "\u05d4\u05d0\u05e1\u05d8\u05e8\u05d8\u05d2\u05d9\u05d4, "
                    "\u05d4\u05d1\u05d9\u05e6\u05d5\u05e2 "
                    "\u05d5\u05d0\u05de\u05d5\u05df "
                    "\u05d4\u05de\u05e9\u05e7\u05d9\u05e2\u05d9\u05dd "
                    "\u05d1\u05d7\u05d1\u05e8\u05d4."
                ),
                market_context=(
                    "\u05d9\u05e9 "
                    "\u05dc\u05d1\u05d3\u05d5\u05e7 "
                    "\u05de\u05d9 "
                    "\u05e2\u05d6\u05d1, "
                    "\u05de\u05d9 "
                    "\u05de\u05d5\u05e0\u05d4 "
                    "\u05d5\u05d4\u05d0\u05dd "
                    "\u05d4\u05e9\u05d9\u05e0\u05d5\u05d9 "
                    "\u05de\u05e8\u05de\u05d6 "
                    "\u05e2\u05dc "
                    "\u05e9\u05d9\u05e0\u05d5\u05d9 "
                    "\u05db\u05d9\u05d5\u05d5\u05df "
                    "\u05d0\u05e1\u05d8\u05e8\u05d8\u05d2\u05d9 "
                    "\u05d0\u05d5 "
                    "\u05e2\u05dc "
                    "\u05d1\u05e2\u05d9\u05d4 "
                    "\u05e4\u05e0\u05d9\u05de\u05d9\u05ea."
                ),
            ),
        )
