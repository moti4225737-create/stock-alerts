from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult


class SecQuarterlyReportRule:
    rule_id = "sec.10q.quarterly_report"
    priority = 300

    def matches(self, event: Event) -> bool:
        return (
            event.source.upper() == "SEC"
            and "10-Q" in event.title.upper()
        )

    def build_summary(self, event: Event) -> str:
        return (
            "\u05d4\u05d7\u05d1\u05e8\u05d4 "
            "\u05e4\u05e8\u05e1\u05de\u05d4 "
            "\u05d3\u05d5\u05d7 "
            "\u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 "
            "\u05d7\u05d3\u05e9 "
            "\u05dc-SEC."
        )

    def build_result(self, event: Event) -> InvestorRuleResult:
        return InvestorRuleResult(
            summary=self.build_summary(event),
            explanation=Explanation(
                why_it_matters=(
                    "\u05ea\u05d5\u05e6\u05d0\u05d5\u05ea "
                    "\u05d5\u05e0\u05ea\u05d5\u05e0\u05d9\u05dd "
                    "\u05ea\u05e4\u05e2\u05d5\u05dc\u05d9\u05d9\u05dd "
                    "\u05e2\u05e9\u05d5\u05d9\u05d9\u05dd "
                    "\u05dc\u05d4\u05e9\u05e4\u05d9\u05e2 "
                    "\u05d1\u05d0\u05d5\u05e4\u05df "
                    "\u05de\u05d4\u05d5\u05ea\u05d9 "
                    "\u05e2\u05dc "
                    "\u05d4\u05e2\u05e8\u05db\u05ea "
                    "\u05d4\u05e9\u05d5\u05d5\u05d9 "
                    "\u05d5\u05e2\u05dc "
                    "\u05e6\u05d9\u05e4\u05d9\u05d5\u05ea "
                    "\u05d4\u05de\u05e9\u05e7\u05d9\u05e2\u05d9\u05dd."
                ),
                market_context=(
                    "\u05d3\u05d9\u05d5\u05d5\u05d7 "
                    "\u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 "
                    "\u05de\u05e9\u05e4\u05d9\u05e2 "
                    "\u05dc\u05e2\u05d9\u05ea\u05d9\u05dd "
                    "\u05e2\u05dc "
                    "\u05e1\u05e0\u05d8\u05d9\u05de\u05e0\u05d8 "
                    "\u05d4\u05e9\u05d5\u05e7 "
                    "\u05d1\u05d8\u05d5\u05d5\u05d7 "
                    "\u05d4\u05e7\u05e6\u05e8 "
                    "\u05d5\u05e2\u05dc "
                    "\u05e2\u05d3\u05db\u05d5\u05e0\u05d9 "
                    "\u05d4\u05e2\u05e8\u05db\u05d5\u05ea "
                    "\u05e9\u05dc "
                    "\u05d0\u05e0\u05dc\u05d9\u05e1\u05d8\u05d9\u05dd."
                ),
            ),
        )
