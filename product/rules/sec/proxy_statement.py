from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult


class SecProxyStatementRule:
    rule_id = "sec.def14a.proxy_statement"
    priority = 300

    def matches(self, event: Event) -> bool:
        return (
            event.source.upper() == "SEC"
            and "DEF 14A" in event.title.upper()
        )

    def build_summary(self, event: Event) -> str:
        return (
            "\u05d4\u05d7\u05d1\u05e8\u05d4 "
            "\u05e4\u05e8\u05e1\u05de\u05d4 "
            "\u05de\u05e1\u05de\u05db\u05d9\u05dd "
            "\u05dc\u05e7\u05e8\u05d0\u05ea "
            "\u05d0\u05e1\u05d9\u05e4\u05ea "
            "\u05d1\u05e2\u05dc\u05d9 "
            "\u05d4\u05de\u05e0\u05d9\u05d5\u05ea."
        )

    def build_result(self, event: Event) -> InvestorRuleResult:
        return InvestorRuleResult(
            summary=self.build_summary(event),
            explanation=Explanation(
                why_it_matters=(
                    "\u05de\u05e1\u05de\u05db\u05d9 "
                    "\u05d4\u05e4\u05e8\u05d5\u05e7\u05e1\u05d9 "
                    "\u05e2\u05e9\u05d5\u05d9\u05d9\u05dd "
                    "\u05dc\u05d7\u05e9\u05d5\u05e3 "
                    "\u05d4\u05d7\u05dc\u05d8\u05d5\u05ea "
                    "\u05de\u05d4\u05d5\u05ea\u05d9\u05d5\u05ea "
                    "\u05e2\u05dc "
                    "\u05d4\u05d4\u05e0\u05d4\u05dc\u05d4, "
                    "\u05ea\u05d2\u05de\u05d5\u05dc "
                    "\u05d5\u05de\u05e9\u05dc "
                    "\u05ea\u05d0\u05d2\u05d9\u05d3\u05d9."
                ),
                market_context=(
                    "\u05d9\u05e9 "
                    "\u05dc\u05d1\u05d3\u05d5\u05e7 "
                    "\u05d0\u05ea "
                    "\u05e1\u05d3\u05e8 "
                    "\u05d4\u05d9\u05d5\u05dd, "
                    "\u05d4\u05d4\u05e6\u05d1\u05e2\u05d5\u05ea "
                    "\u05d4\u05de\u05d5\u05e6\u05e2\u05d5\u05ea, "
                    "\u05d4\u05de\u05d5\u05e2\u05de\u05d3\u05d9\u05dd "
                    "\u05dc\u05d3\u05d9\u05e8\u05e7\u05d8\u05d5\u05e8\u05d9\u05d5\u05df "
                    "\u05d5\u05de\u05d3\u05d9\u05e0\u05d9\u05d5\u05ea "
                    "\u05d4\u05ea\u05d2\u05de\u05d5\u05dc."
                ),
            ),
        )
