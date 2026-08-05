from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult


class SecShelfRegistrationRule:
    rule_id = "sec.s3.shelf_registration"
    priority = 300

    def matches(self, event: Event) -> bool:
        return (
            event.source.upper() == "SEC"
            and "S-3" in event.title.upper()
        )

    def build_summary(self, event: Event) -> str:
        return (
            "\u05d4\u05d7\u05d1\u05e8\u05d4 "
            "\u05d4\u05d2\u05d9\u05e9\u05d4 "
            "\u05dc-SEC "
            "\u05ea\u05e9\u05e7\u05d9\u05e3 "
            "\u05de\u05d3\u05e3 "
            "\u05e9\u05e2\u05e9\u05d5\u05d9 "
            "\u05dc\u05d0\u05e4\u05e9\u05e8 "
            "\u05d2\u05d9\u05d5\u05e1 "
            "\u05d4\u05d5\u05df "
            "\u05e2\u05ea\u05d9\u05d3\u05d9."
        )

    def build_result(self, event: Event) -> InvestorRuleResult:
        return InvestorRuleResult(
            summary=self.build_summary(event),
            explanation=Explanation(
                why_it_matters=(
                    "\u05ea\u05e9\u05e7\u05d9\u05e3 "
                    "\u05de\u05d3\u05e3 "
                    "\u05e2\u05e9\u05d5\u05d9 "
                    "\u05dc\u05d0\u05e4\u05e9\u05e8 "
                    "\u05dc\u05d7\u05d1\u05e8\u05d4 "
                    "\u05dc\u05d2\u05d9\u05d9\u05e1 "
                    "\u05d4\u05d5\u05df "
                    "\u05d1\u05e2\u05ea\u05d9\u05d3 "
                    "\u05d5\u05dc\u05d4\u05d2\u05d3\u05d9\u05dc "
                    "\u05d0\u05ea "
                    "\u05e1\u05d9\u05db\u05d5\u05df "
                    "\u05d4\u05d3\u05d9\u05dc\u05d5\u05dc."
                ),
                market_context=(
                    "\u05d9\u05e9 "
                    "\u05dc\u05d1\u05d3\u05d5\u05e7 "
                    "\u05d0\u05ea "
                    "\u05d4\u05d9\u05e7\u05e3 "
                    "\u05d4\u05de\u05e8\u05d1\u05d9 "
                    "\u05e9\u05dc "
                    "\u05d4\u05d2\u05d9\u05d5\u05e1, "
                    "\u05e1\u05d5\u05d2\u05d9 "
                    "\u05e0\u05d9\u05d9\u05e8\u05d5\u05ea "
                    "\u05d4\u05e2\u05e8\u05da "
                    "\u05d5\u05d4\u05d0\u05dd "
                    "\u05e4\u05d5\u05e8\u05e1\u05de\u05d4 "
                    "\u05d4\u05e6\u05e2\u05d4 "
                    "\u05e7\u05d5\u05e0\u05e7\u05e8\u05d8\u05d9\u05ea."
                ),
            ),
        )
