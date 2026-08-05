from models.event import Event
from product.rules.fda.drug_recall import FdaDrugRecallSummaryRule


def make_event(
    title: str = "FDA Drug Recall — Class II — Liquidia Technologies",
    summary: str = (
        "Example recall reason"
        " | Product: Example drug product"
        " | Recall number: D-1234"
        " | Status: Ongoing"
    ),
    source: str = "FDA",
) -> Event:
    return Event(
        symbol="LQDA",
        source=source,
        title=title,
        summary=summary,
        published_at="2026-08-05T10:00:00+00:00",
        importance=8,
        sentiment="negative",
    )


def test_fda_recall_rule_matches_expected_event():
    rule = FdaDrugRecallSummaryRule()
    event = make_event()

    assert rule.rule_id == "fda.drug_recall"
    assert rule.priority == 300
    assert rule.matches(event) is True
    assert rule.build_summary(event) == (
        "ה-FDA פרסם הודעת החזרה מהשוק "
        "מסוג Class II למוצר של החברה."
    )


def test_fda_recall_rule_rejects_wrong_source():
    rule = FdaDrugRecallSummaryRule()

    assert rule.matches(make_event(source="NEWS")) is False


def test_fda_recall_rule_rejects_unrelated_title():
    rule = FdaDrugRecallSummaryRule()

    assert rule.matches(
        make_event(title="FDA Approval Decision")
    ) is False

def test_fda_recall_rule_distinguishes_class_i():
    rule = FdaDrugRecallSummaryRule()
    event = make_event(
        title="FDA Drug Recall — Class I — Liquidia Technologies"
    )

    assert rule.build_summary(event) == (
        "ה-FDA פרסם הודעת החזרה מהשוק "
        "מסוג Class I למוצר של החברה."
    )


def test_fda_recall_rule_distinguishes_class_iii():
    rule = FdaDrugRecallSummaryRule()
    event = make_event(
        title="FDA Drug Recall — Class III — Liquidia Technologies"
    )

    assert rule.build_summary(event) == (
        "ה-FDA פרסם הודעת החזרה מהשוק "
        "מסוג Class III למוצר של החברה."
    )


def test_fda_recall_rule_builds_generic_summary_without_classification():
    rule = FdaDrugRecallSummaryRule()
    event = make_event(
        title="FDA Drug Recall — Liquidia Technologies"
    )

    assert rule.build_summary(event) == (
        "ה-FDA פרסם הודעת החזרה מהשוק למוצר של החברה."
    )
