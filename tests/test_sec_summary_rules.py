from models.event import Event
from product.investor_summary_rule_set import InvestorSummaryRuleSet
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


def make_event(
    source: str = "SEC",
    title: str = "SEC Filing: 8-K",
    summary: str = "Entry into a Material Definitive Agreement",
) -> Event:
    return Event(
        symbol="LQDA",
        source=source,
        title=title,
        summary=summary,
        published_at="2026-08-05T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )


def test_material_agreement_rule_matches_expected_sec_event():
    rule = SecMaterialAgreementSummaryRule()

    assert rule.rule_id == "sec.8k.material_agreement"
    assert rule.priority == 300
    assert rule.matches(make_event()) is True
    assert rule.build_summary(make_event()) == (
        "החברה דיווחה על התקשרות בהסכם מהותי חדש."
    )


def test_material_agreement_rule_rejects_wrong_source():
    rule = SecMaterialAgreementSummaryRule()

    assert rule.matches(make_event(source="NEWS")) is False


def test_material_agreement_rule_rejects_wrong_form():
    rule = SecMaterialAgreementSummaryRule()

    assert rule.matches(
        make_event(title="SEC Filing: 10-Q")
    ) is False


def test_material_agreement_rule_rejects_unrelated_description():
    rule = SecMaterialAgreementSummaryRule()

    assert rule.matches(
        make_event(summary="Results of Operations and Financial Condition")
    ) is False

def test_generic_8k_rule_matches_sec_8k_event():
    rule = Sec8KSummaryRule()

    assert rule.rule_id == "sec.8k.generic"
    assert rule.priority == 100
    assert rule.matches(
        make_event(summary="Unrecognized SEC description")
    ) is True
    assert rule.build_summary(make_event()) == (
        "החברה פרסמה דיווח מיידי על אירוע מהותי ל-SEC."
    )


def test_generic_8k_rule_rejects_wrong_source_or_form():
    rule = Sec8KSummaryRule()

    assert rule.matches(make_event(source="NEWS")) is False
    assert rule.matches(
        make_event(title="SEC Filing: 10-Q")
    ) is False


def test_specific_sec_rule_wins_over_generic_8k_rule():
    rule_set = InvestorSummaryRuleSet(
        rules=(
            Sec8KSummaryRule(),
            SecMaterialAgreementSummaryRule(),
        )
    )

    assert rule_set.build(make_event()) == (
        "החברה דיווחה על התקשרות בהסכם מהותי חדש."
    )

def test_financial_results_rule_matches_expected_sec_event():
    rule = SecFinancialResultsSummaryRule()
    event = make_event(
        summary="Results of Operations and Financial Condition"
    )

    assert rule.rule_id == "sec.8k.financial_results"
    assert rule.priority == 300
    assert rule.matches(event) is True
    assert rule.build_summary(event) == (
        "החברה דיווחה על תוצאותיה הכספיות."
    )


def test_financial_results_rule_rejects_unrelated_event():
    rule = SecFinancialResultsSummaryRule()

    assert rule.matches(
        make_event(summary="Unrecognized SEC description")
    ) is False


def test_leadership_change_rule_matches_expected_sec_event():
    rule = SecLeadershipChangeSummaryRule()
    event = make_event(
        summary=(
            "Departure of Directors or Certain Officers; "
            "Election of Directors; Appointment of Certain Officers"
        )
    )

    assert rule.rule_id == "sec.8k.leadership_change"
    assert rule.priority == 300
    assert rule.matches(event) is True
    assert rule.build_summary(event) == (
        "החברה דיווחה על שינוי בהנהלה או בדירקטוריון."
    )


def test_leadership_change_rule_rejects_unrelated_event():
    rule = SecLeadershipChangeSummaryRule()

    assert rule.matches(
        make_event(summary="Unrecognized SEC description")
    ) is False


def test_specific_content_rules_win_over_generic_8k_rule():
    rule_set = InvestorSummaryRuleSet(
        rules=(
            Sec8KSummaryRule(),
            SecMaterialAgreementSummaryRule(),
            SecFinancialResultsSummaryRule(),
            SecLeadershipChangeSummaryRule(),
        )
    )

    financial_event = make_event(
        summary="Results of Operations and Financial Condition"
    )
    leadership_event = make_event(
        summary="Appointment of Certain Officers"
    )

    assert rule_set.build(financial_event) == (
        "החברה דיווחה על תוצאותיה הכספיות."
    )
    assert rule_set.build(leadership_event) == (
        "החברה דיווחה על שינוי בהנהלה או בדירקטוריון."
    )