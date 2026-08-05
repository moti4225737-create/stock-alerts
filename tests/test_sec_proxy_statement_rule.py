from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult
from product.rules.sec.proxy_statement import (
    SecProxyStatementRule,
)


def make_event() -> Event:
    return Event(
        symbol="AAPL",
        source="SEC",
        title="SEC Filing: DEF 14A",
        summary="Proxy statement",
        published_at="2026-08-05T10:00:00+00:00",
        importance=6,
        sentiment="neutral",
    )


def test_proxy_statement_rule_matches_def_14a():
    rule = SecProxyStatementRule()
    event = make_event()

    assert rule.rule_id == "sec.def14a.proxy_statement"
    assert rule.priority == 300
    assert rule.matches(event) is True


def test_proxy_statement_rule_rejects_wrong_form():
    rule = SecProxyStatementRule()

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


def test_proxy_statement_rule_builds_structured_interpretation():
    rule = SecProxyStatementRule()
    event = make_event()

    assert rule.build_result(event) == InvestorRuleResult(
        summary=(
            "\u05d4\u05d7\u05d1\u05e8\u05d4 "
            "\u05e4\u05e8\u05e1\u05de\u05d4 "
            "\u05de\u05e1\u05de\u05db\u05d9\u05dd "
            "\u05dc\u05e7\u05e8\u05d0\u05ea "
            "\u05d0\u05e1\u05d9\u05e4\u05ea "
            "\u05d1\u05e2\u05dc\u05d9 "
            "\u05d4\u05de\u05e0\u05d9\u05d5\u05ea."
        ),
        explanation=Explanation(
            why_it_matters=(
                "\u05de\u05e1\u05de\u05db\u05d9 "
                "\u05d4\u05e4\u05e8\u05d5\u05e7\u05e1\u05d9 "
                "\u05e2\u05e9\u05d5\u05d9\u05d9\u05dd "
                "\u05dc\u05d7\u05e9\u05d5\u05e3 "
                "\u05d4\u05d7\u05dc\u05d8\u05d5\u05ea "
                "\u05de\u05d4\u05d5\u05ea\u05d9\u05d5\u05ea "
                "\u05e2\u05dc "
                "\u05d4\u05d4\u05e0\u05d4\u05dc\u05d4, "
                "\u05ea\u05d2\u05de\u05d5\u05dc "
                "\u05d5\u05de\u05e9\u05dc "
                "\u05ea\u05d0\u05d2\u05d9\u05d3\u05d9."
            ),
            market_context=(
                "\u05d9\u05e9 "
                "\u05dc\u05d1\u05d3\u05d5\u05e7 "
                "\u05d0\u05ea "
                "\u05e1\u05d3\u05e8 "
                "\u05d4\u05d9\u05d5\u05dd, "
                "\u05d4\u05d4\u05e6\u05d1\u05e2\u05d5\u05ea "
                "\u05d4\u05de\u05d5\u05e6\u05e2\u05d5\u05ea, "
                "\u05d4\u05de\u05d5\u05e2\u05de\u05d3\u05d9\u05dd "
                "\u05dc\u05d3\u05d9\u05e8\u05e7\u05d8\u05d5\u05e8\u05d9\u05d5\u05df "
                "\u05d5\u05de\u05d3\u05d9\u05e0\u05d9\u05d5\u05ea "
                "\u05d4\u05ea\u05d2\u05de\u05d5\u05dc."
            ),
        ),
    )
