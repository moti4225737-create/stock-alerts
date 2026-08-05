from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult
from product.rules.sec.annual_report import (
    SecAnnualReportRule,
)


def make_event() -> Event:
    return Event(
        symbol="AAPL",
        source="SEC",
        title="SEC Filing: 10-K",
        summary="Annual report",
        published_at="2026-08-05T10:00:00+00:00",
        importance=7,
        sentiment="neutral",
    )


def test_annual_report_rule_matches_sec_10k():
    rule = SecAnnualReportRule()
    event = make_event()

    assert rule.rule_id == "sec.10k.annual_report"
    assert rule.priority == 300
    assert rule.matches(event) is True


def test_annual_report_rule_rejects_wrong_form():
    rule = SecAnnualReportRule()

    event = Event(
        symbol="AAPL",
        source="SEC",
        title="SEC Filing: 10-Q",
        summary="Quarterly report",
        published_at="2026-08-05T10:00:00+00:00",
        importance=7,
        sentiment="neutral",
    )

    assert rule.matches(event) is False


def test_annual_report_rule_builds_structured_interpretation():
    rule = SecAnnualReportRule()
    event = make_event()

    assert rule.build_result(event) == InvestorRuleResult(
        summary=(
            "\u05d4\u05d7\u05d1\u05e8\u05d4 "
            "\u05e4\u05e8\u05e1\u05de\u05d4 "
            "\u05d0\u05ea "
            "\u05d4\u05d3\u05d5\u05d7 "
            "\u05d4\u05e9\u05e0\u05ea\u05d9 "
            "\u05e9\u05dc\u05d4 "
            "\u05dc-SEC."
        ),
        explanation=Explanation(
            why_it_matters=(
                "\u05d3\u05d5\u05d7 "
                "\u05e9\u05e0\u05ea\u05d9 "
                "\u05de\u05e8\u05db\u05d6 "
                "\u05d0\u05ea "
                "\u05d4\u05d1\u05d9\u05e6\u05d5\u05e2\u05d9\u05dd, "
                "\u05d4\u05e1\u05d9\u05db\u05d5\u05e0\u05d9\u05dd "
                "\u05d5\u05d4\u05de\u05d2\u05de\u05d5\u05ea "
                "\u05d4\u05de\u05e8\u05db\u05d6\u05d9\u05d5\u05ea "
                "\u05e9\u05dc "
                "\u05d4\u05d7\u05d1\u05e8\u05d4."
            ),
            market_context=(
                "\u05d9\u05e9 "
                "\u05dc\u05d1\u05d7\u05d5\u05df "
                "\u05d0\u05ea "
                "\u05d4\u05d4\u05db\u05e0\u05e1\u05d5\u05ea, "
                "\u05d4\u05e8\u05d5\u05d5\u05d7\u05d9\u05d5\u05ea, "
                "\u05ea\u05d6\u05e8\u05d9\u05dd "
                "\u05d4\u05de\u05d6\u05d5\u05de\u05e0\u05d9\u05dd, "
                "\u05d4\u05d7\u05d5\u05d1 "
                "\u05d5\u05d2\u05d5\u05e8\u05de\u05d9 "
                "\u05d4\u05e1\u05d9\u05db\u05d5\u05df "
                "\u05dc\u05e2\u05d5\u05de\u05ea "
                "\u05d4\u05e9\u05e0\u05d4 "
                "\u05d4\u05e7\u05d5\u05d3\u05de\u05ea."
            ),
        ),
    )
