from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult


class FdaDrugRecallSummaryRule:
    rule_id = "fda.drug_recall"
    priority = 300

    def matches(self, event: Event) -> bool:
        return (
            event.source.upper() == "FDA"
            and "DRUG RECALL" in event.title.upper()
        )

    def build_summary(self, event: Event) -> str:
        title = event.title.upper()

        if "CLASS III" in title:
            classification = "Class III"
        elif "CLASS II" in title:
            classification = "Class II"
        elif "CLASS I" in title:
            classification = "Class I"
        else:
            classification = None

        if classification is None:
            return (
                "\u05d4-FDA "
                "\u05e4\u05e8\u05e1\u05dd "
                "\u05d4\u05d5\u05d3\u05e2\u05ea "
                "\u05d4\u05d7\u05d6\u05e8\u05d4 "
                "\u05de\u05d4\u05e9\u05d5\u05e7 "
                "\u05dc\u05de\u05d5\u05e6\u05e8 "
                "\u05e9\u05dc "
                "\u05d4\u05d7\u05d1\u05e8\u05d4."
            )

        return (
            "\u05d4-FDA "
            "\u05e4\u05e8\u05e1\u05dd "
            "\u05d4\u05d5\u05d3\u05e2\u05ea "
            "\u05d4\u05d7\u05d6\u05e8\u05d4 "
            "\u05de\u05d4\u05e9\u05d5\u05e7 "
            f"\u05de\u05e1\u05d5\u05d2 {classification} "
            "\u05dc\u05de\u05d5\u05e6\u05e8 "
            "\u05e9\u05dc "
            "\u05d4\u05d7\u05d1\u05e8\u05d4."
        )

    def build_result(self, event: Event) -> InvestorRuleResult:
        return InvestorRuleResult(
            summary=self.build_summary(event),
            explanation=Explanation(
                why_it_matters=(
                    "\u05d4\u05d7\u05d6\u05e8\u05ea "
                    "\u05ea\u05e8\u05d5\u05e4\u05d4 "
                    "\u05de\u05d4\u05e9\u05d5\u05e7 "
                    "\u05e2\u05e9\u05d5\u05d9\u05d4 "
                    "\u05dc\u05d4\u05e9\u05e4\u05d9\u05e2 "
                    "\u05e2\u05dc "
                    "\u05d4\u05de\u05db\u05d9\u05e8\u05d5\u05ea, "
                    "\u05d4\u05de\u05d5\u05e0\u05d9\u05d8\u05d9\u05df "
                    "\u05d5\u05d4\u05d7\u05e9\u05d9\u05e4\u05d4 "
                    "\u05d4\u05de\u05e9\u05e4\u05d8\u05d9\u05ea "
                    "\u05e9\u05dc "
                    "\u05d4\u05d7\u05d1\u05e8\u05d4."
                ),
                market_context=(
                    "\u05d9\u05e9 "
                    "\u05dc\u05d1\u05d3\u05d5\u05e7 "
                    "\u05d0\u05ea "
                    "\u05d3\u05e8\u05d2\u05ea "
                    "\u05d4\u05e1\u05d9\u05db\u05d5\u05df, "
                    "\u05d4\u05de\u05d5\u05e6\u05e8\u05d9\u05dd "
                    "\u05d4\u05de\u05d5\u05e9\u05e4\u05e2\u05d9\u05dd, "
                    "\u05e1\u05d9\u05d1\u05ea "
                    "\u05d4\u05d4\u05d7\u05d6\u05e8\u05d4 "
                    "\u05d5\u05d4\u05d0\u05dd "
                    "\u05d4\u05d0\u05d9\u05e8\u05d5\u05e2 "
                    "\u05e6\u05e4\u05d5\u05d9 "
                    "\u05dc\u05d4\u05ea\u05e8\u05d7\u05d1."
                ),
            ),
        )
