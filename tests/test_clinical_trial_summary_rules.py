from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult
from product.rules.clinical_trials.status_update import (
    ClinicalTrialStatusSummaryRule,
)


def make_event(
    summary: str,
    source: str = "ClinicalTrials.gov",
    title: str = "Clinical Trial \u2014 Yutrepia Study",
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


def test_clinical_trial_rule_builds_recruiting_summary():
    rule = ClinicalTrialStatusSummaryRule()
    event = make_event(
        "NCT ID: NCT01234567 | Status: RECRUITING"
    )

    assert rule.rule_id == "clinical_trials.status"
    assert rule.priority == 300
    assert rule.matches(event) is True
    assert rule.build_summary(event) == (
        "\u05d4\u05e0\u05d9\u05e1\u05d5\u05d9 "
        "\u05d4\u05e7\u05dc\u05d9\u05e0\u05d9 "
        "\u05e0\u05de\u05e6\u05d0 "
        "\u05db\u05e2\u05ea "
        "\u05d1\u05e1\u05d8\u05d8\u05d5\u05e1 Recruiting."
    )


def test_clinical_trial_rule_builds_completed_summary():
    rule = ClinicalTrialStatusSummaryRule()
    event = make_event(
        "NCT ID: NCT01234567 | Status: COMPLETED"
    )

    assert rule.build_summary(event) == (
        "\u05d4\u05e0\u05d9\u05e1\u05d5\u05d9 "
        "\u05d4\u05e7\u05dc\u05d9\u05e0\u05d9 "
        "\u05d4\u05d5\u05e9\u05dc\u05dd."
    )


def test_clinical_trial_rule_rejects_wrong_source():
    rule = ClinicalTrialStatusSummaryRule()

    assert rule.matches(
        make_event(
            "Status: RECRUITING",
            source="NEWS",
        )
    ) is False


def test_clinical_trial_rule_rejects_missing_status():
    rule = ClinicalTrialStatusSummaryRule()

    assert rule.matches(
        make_event("NCT ID: NCT01234567")
    ) is False


def test_clinical_trial_rule_builds_structured_interpretation():
    rule = ClinicalTrialStatusSummaryRule()
    event = make_event(
        "NCT ID: NCT01234567 | Status: RECRUITING"
    )

    result = rule.build_result(event)

    assert result == InvestorRuleResult(
        summary=rule.build_summary(event),
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
