from models.event import Event
from product.investor_summary_rule_set import InvestorSummaryRuleSet
from product.rules.clinical_trials.status_update import (
    ClinicalTrialStatusSummaryRule,
)
from product.rules.fda.drug_recall import FdaDrugRecallSummaryRule
from product.rules.sec.financial_results import (
    SecFinancialResultsSummaryRule,
)
from product.rules.sec.generic_8k import Sec8KSummaryRule
from product.rules.sec.leadership_change import (
    SecLeadershipChangeSummaryRule,
)
from product.rules.sec.material_agreement import (
    SecMaterialAgreementSummaryRule,
)


class InvestorSummaryPolicy:
    def __init__(
        self,
        rule_set: InvestorSummaryRuleSet | None = None,
    ) -> None:
        self._rule_set = rule_set or InvestorSummaryRuleSet(
            rules=(
                SecMaterialAgreementSummaryRule(),
                SecFinancialResultsSummaryRule(),
                SecLeadershipChangeSummaryRule(),
                FdaDrugRecallSummaryRule(),
                ClinicalTrialStatusSummaryRule(),
                Sec8KSummaryRule(),
            )
        )

    def build(self, event: Event) -> str:
        rule_summary = self._rule_set.build(event)

        if rule_summary != event.summary:
            return rule_summary

        source = event.source.upper()
        title = event.title.upper()

        if source == "SEC" and "10-Q" in title:
            return "החברה פרסמה דוח רבעוני חדש ל-SEC."

        if source == "SEC" and "10-K" in title:
            return "החברה פרסמה את הדוח השנתי שלה ל-SEC."

        if source == "SEC" and "DEF 14A" in title:
            return (
                "החברה פרסמה מסמכים "
                "לקראת אסיפת בעלי המניות."
            )

        if source == "SEC" and "S-3" in title:
            return (
                "החברה הגישה ל-SEC תשקיף מדף "
                "שעשוי לאפשר גיוס הון עתידי."
            )

        return event.summary
