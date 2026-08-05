from models.event import Event
from product.rules.clinical_trials.status_update import (
    ClinicalTrialStatusSummaryRule,
)


def make_event(
    summary: str,
    source: str = "ClinicalTrials.gov",
    title: str = "Clinical Trial — Yutrepia Study",
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
        "הניסוי הקליני נמצא כעת בסטטוס Recruiting."
    )


def test_clinical_trial_rule_builds_completed_summary():
    rule = ClinicalTrialStatusSummaryRule()
    event = make_event(
        "NCT ID: NCT01234567 | Status: COMPLETED"
    )

    assert rule.build_summary(event) == (
        "הניסוי הקליני הושלם."
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
