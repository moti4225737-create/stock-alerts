from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult
from product.rules.sec.shelf_registration import (
    SecShelfRegistrationRule,
)


def make_event() -> Event:
    return Event(
        symbol="AAPL",
        source="SEC",
        title="SEC Filing: S-3",
        summary="Shelf registration",
        published_at="2026-08-05T10:00:00+00:00",
        importance=7,
        sentiment="neutral",
    )


def test_shelf_registration_rule_matches_sec_s3():
    rule = SecShelfRegistrationRule()
    event = make_event()

    assert rule.rule_id == "sec.s3.shelf_registration"
    assert rule.priority == 300
    assert rule.matches(event) is True


def test_shelf_registration_rule_rejects_wrong_form():
    rule = SecShelfRegistrationRule()

    event = Event(
        symbol="AAPL",
        source="SEC",
        title="SEC Filing: 10-K",
        summary="Annual report",
        published_at="2026-08-05T10:00:00+00:00",
        importance=7,
        sentiment="neutral",
    )

    assert rule.matches(event) is False


def test_shelf_registration_rule_builds_structured_interpretation():
    rule = SecShelfRegistrationRule()
    event = make_event()

    assert rule.build_result(event) == InvestorRuleResult(
        summary=(
            "\u05d4\u05d7\u05d1\u05e8\u05d4 "
            "\u05d4\u05d2\u05d9\u05e9\u05d4 "
            "\u05dc-SEC "
            "\u05ea\u05e9\u05e7\u05d9\u05e3 "
            "\u05de\u05d3\u05e3 "
            "\u05e9\u05e2\u05e9\u05d5\u05d9 "
            "\u05dc\u05d0\u05e4\u05e9\u05e8 "
            "\u05d2\u05d9\u05d5\u05e1 "
            "\u05d4\u05d5\u05df "
            "\u05e2\u05ea\u05d9\u05d3\u05d9."
        ),
        explanation=Explanation(
            why_it_matters=(
                "\u05ea\u05e9\u05e7\u05d9\u05e3 "
                "\u05de\u05d3\u05e3 "
                "\u05e2\u05e9\u05d5\u05d9 "
                "\u05dc\u05d0\u05e4\u05e9\u05e8 "
                "\u05dc\u05d7\u05d1\u05e8\u05d4 "
                "\u05dc\u05d2\u05d9\u05d9\u05e1 "
                "\u05d4\u05d5\u05df "
                "\u05d1\u05e2\u05ea\u05d9\u05d3 "
                "\u05d5\u05dc\u05d4\u05d2\u05d3\u05d9\u05dc "
                "\u05d0\u05ea "
                "\u05e1\u05d9\u05db\u05d5\u05df "
                "\u05d4\u05d3\u05d9\u05dc\u05d5\u05dc."
            ),
            market_context=(
                "\u05d9\u05e9 "
                "\u05dc\u05d1\u05d3\u05d5\u05e7 "
                "\u05d0\u05ea "
                "\u05d4\u05d9\u05e7\u05e3 "
                "\u05d4\u05de\u05e8\u05d1\u05d9 "
                "\u05e9\u05dc "
                "\u05d4\u05d2\u05d9\u05d5\u05e1, "
                "\u05e1\u05d5\u05d2\u05d9 "
                "\u05e0\u05d9\u05d9\u05e8\u05d5\u05ea "
                "\u05d4\u05e2\u05e8\u05da "
                "\u05d5\u05d4\u05d0\u05dd "
                "\u05e4\u05d5\u05e8\u05e1\u05de\u05d4 "
                "\u05d4\u05e6\u05e2\u05d4 "
                "\u05e7\u05d5\u05e0\u05e7\u05e8\u05d8\u05d9\u05ea."
            ),
        ),
    )
