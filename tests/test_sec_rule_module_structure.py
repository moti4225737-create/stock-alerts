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


def test_sec_rules_are_exposed_from_dedicated_modules():
    assert SecMaterialAgreementSummaryRule.rule_id == (
        "sec.8k.material_agreement"
    )
    assert SecFinancialResultsSummaryRule.rule_id == (
        "sec.8k.financial_results"
    )
    assert SecLeadershipChangeSummaryRule.rule_id == (
        "sec.8k.leadership_change"
    )
    assert Sec8KSummaryRule.rule_id == "sec.8k.generic"