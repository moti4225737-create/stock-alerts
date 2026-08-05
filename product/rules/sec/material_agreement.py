from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult


class SecMaterialAgreementSummaryRule:
    rule_id = "sec.8k.material_agreement"
    priority = 300

    _PATTERN = "ENTRY INTO A MATERIAL DEFINITIVE AGREEMENT"

    def matches(self, event: Event) -> bool:
        return (
            event.source.upper() == "SEC"
            and "8-K" in event.title.upper()
            and self._PATTERN in event.summary.upper()
        )

    def build_summary(self, event: Event) -> str:
        return (
            "\u05d4\u05d7\u05d1\u05e8\u05d4 "
            "\u05d3\u05d9\u05d5\u05d5\u05d7\u05d4 "
            "\u05e2\u05dc "
            "\u05d4\u05ea\u05e7\u05e9\u05e8\u05d5\u05ea "
            "\u05d1\u05d4\u05e1\u05db\u05dd "
            "\u05de\u05d4\u05d5\u05ea\u05d9 "
            "\u05d7\u05d3\u05e9."
        )

    def build_result(self, event: Event) -> InvestorRuleResult:
        return InvestorRuleResult(
            summary=self.build_summary(event),
            explanation=Explanation(
                why_it_matters=(
                    "\u05d4\u05e1\u05db\u05dd "
                    "\u05de\u05d4\u05d5\u05ea\u05d9 "
                    "\u05e2\u05e9\u05d5\u05d9 "
                    "\u05dc\u05e9\u05e0\u05d5\u05ea "
                    "\u05d0\u05ea "
                    "\u05d4\u05ea\u05d7\u05d9\u05d9\u05d1\u05d5\u05d9\u05d5\u05ea "
                    "\u05d4\u05d7\u05d1\u05e8\u05d4, "
                    "\u05de\u05e7\u05d5\u05e8\u05d5\u05ea "
                    "\u05d4\u05d4\u05db\u05e0\u05e1\u05d4 "
                    "\u05e9\u05dc\u05d4 "
                    "\u05d0\u05d5 "
                    "\u05d4\u05e1\u05d9\u05db\u05d5\u05e0\u05d9\u05dd "
                    "\u05d4\u05e2\u05e1\u05e7\u05d9\u05d9\u05dd "
                    "\u05e9\u05dc\u05d4."
                ),
                market_context=(
                    "\u05d9\u05e9 "
                    "\u05dc\u05d1\u05d7\u05d5\u05df "
                    "\u05d0\u05ea "
                    "\u05d4\u05e6\u05d3\u05d3\u05d9\u05dd "
                    "\u05dc\u05d4\u05e1\u05db\u05dd, "
                    "\u05d4\u05d9\u05e7\u05e4\u05d5, "
                    "\u05ea\u05e0\u05d0\u05d9\u05d5 "
                    "\u05d5\u05d4\u05e9\u05e4\u05e2\u05ea\u05d5 "
                    "\u05d4\u05d0\u05e4\u05e9\u05e8\u05d9\u05ea "
                    "\u05e2\u05dc "
                    "\u05d4\u05ea\u05d7\u05d6\u05d9\u05ea "
                    "\u05d4\u05e4\u05d9\u05e0\u05e0\u05e1\u05d9\u05ea."
                ),
            ),
        )
