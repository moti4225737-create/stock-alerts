from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult
from product.rules.fda.drug_recall import FdaDrugRecallSummaryRule


def make_event(
    title: str = (
        "FDA Drug Recall ? Class II ? Liquidia Technologies"
    ),
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
        "\u05d4-FDA "
        "\u05e4\u05e8\u05e1\u05dd "
        "\u05d4\u05d5\u05d3\u05e2\u05ea "
        "\u05d4\u05d7\u05d6\u05e8\u05d4 "
        "\u05de\u05d4\u05e9\u05d5\u05e7 "
        "\u05de\u05e1\u05d5\u05d2 Class II "
        "\u05dc\u05de\u05d5\u05e6\u05e8 "
        "\u05e9\u05dc "
        "\u05d4\u05d7\u05d1\u05e8\u05d4."
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
        title="FDA Drug Recall ? Class I ? Liquidia Technologies"
    )

    assert rule.build_summary(event) == (
        "\u05d4-FDA "
        "\u05e4\u05e8\u05e1\u05dd "
        "\u05d4\u05d5\u05d3\u05e2\u05ea "
        "\u05d4\u05d7\u05d6\u05e8\u05d4 "
        "\u05de\u05d4\u05e9\u05d5\u05e7 "
        "\u05de\u05e1\u05d5\u05d2 Class I "
        "\u05dc\u05de\u05d5\u05e6\u05e8 "
        "\u05e9\u05dc "
        "\u05d4\u05d7\u05d1\u05e8\u05d4."
    )


def test_fda_recall_rule_distinguishes_class_iii():
    rule = FdaDrugRecallSummaryRule()
    event = make_event(
        title="FDA Drug Recall ? Class III ? Liquidia Technologies"
    )

    assert rule.build_summary(event) == (
        "\u05d4-FDA "
        "\u05e4\u05e8\u05e1\u05dd "
        "\u05d4\u05d5\u05d3\u05e2\u05ea "
        "\u05d4\u05d7\u05d6\u05e8\u05d4 "
        "\u05de\u05d4\u05e9\u05d5\u05e7 "
        "\u05de\u05e1\u05d5\u05d2 Class III "
        "\u05dc\u05de\u05d5\u05e6\u05e8 "
        "\u05e9\u05dc "
        "\u05d4\u05d7\u05d1\u05e8\u05d4."
    )


def test_fda_recall_rule_builds_generic_summary_without_classification():
    rule = FdaDrugRecallSummaryRule()
    event = make_event(
        title="FDA Drug Recall ? Liquidia Technologies"
    )

    assert rule.build_summary(event) == (
        "\u05d4-FDA "
        "\u05e4\u05e8\u05e1\u05dd "
        "\u05d4\u05d5\u05d3\u05e2\u05ea "
        "\u05d4\u05d7\u05d6\u05e8\u05d4 "
        "\u05de\u05d4\u05e9\u05d5\u05e7 "
        "\u05dc\u05de\u05d5\u05e6\u05e8 "
        "\u05e9\u05dc "
        "\u05d4\u05d7\u05d1\u05e8\u05d4."
    )


def test_fda_recall_rule_builds_structured_interpretation():
    rule = FdaDrugRecallSummaryRule()
    event = make_event()

    result = rule.build_result(event)

    assert result == InvestorRuleResult(
        summary=rule.build_summary(event),
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
