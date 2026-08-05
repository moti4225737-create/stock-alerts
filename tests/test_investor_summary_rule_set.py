from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult
from product.investor_summary_rule_set import InvestorSummaryRuleSet


class FakeRule:
    def __init__(
        self,
        rule_id: str,
        priority: int,
        matches: bool,
        summary: str,
    ) -> None:
        self.rule_id = rule_id
        self.priority = priority
        self._matches = matches
        self._summary = summary
        self.received_events: list[Event] = []

    def matches(self, event: Event) -> bool:
        self.received_events.append(event)
        return self._matches

    def build_summary(self, event: Event) -> str:
        return self._summary


def make_event() -> Event:
    return Event(
        symbol="LQDA",
        source="SEC",
        title="SEC Filing: 8-K",
        summary="Raw provider summary",
        published_at="2026-08-05T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )


def test_higher_priority_matching_rule_wins():
    lower_priority_rule = FakeRule(
        rule_id="lower",
        priority=10,
        matches=True,
        summary="Lower priority summary",
    )
    higher_priority_rule = FakeRule(
        rule_id="higher",
        priority=100,
        matches=True,
        summary="Higher priority summary",
    )

    rule_set = InvestorSummaryRuleSet(
        rules=(
            lower_priority_rule,
            higher_priority_rule,
        )
    )

    assert rule_set.build(make_event()) == "Higher priority summary"


def test_first_matching_rule_stops_evaluation():
    first_rule = FakeRule(
        rule_id="first",
        priority=100,
        matches=True,
        summary="First summary",
    )
    second_rule = FakeRule(
        rule_id="second",
        priority=10,
        matches=True,
        summary="Second summary",
    )

    event = make_event()
    rule_set = InvestorSummaryRuleSet(
        rules=(second_rule, first_rule)
    )

    assert rule_set.build(event) == "First summary"
    assert first_rule.received_events == [event]
    assert second_rule.received_events == []


def test_returns_event_summary_when_no_rule_matches():
    rule = FakeRule(
        rule_id="non_matching",
        priority=100,
        matches=False,
        summary="Unused summary",
    )

    event = make_event()
    rule_set = InvestorSummaryRuleSet(rules=(rule,))

    assert rule_set.build(event) == "Raw provider summary"


class StructuredFakeRule:
    rule_id = "structured"
    priority = 100

    def matches(self, event: Event) -> bool:
        return True

    def build_result(self, event: Event) -> InvestorRuleResult:
        return InvestorRuleResult(
            summary="Structured summary",
            explanation=Explanation(
                why_it_matters="Structured importance explanation",
                market_context="Structured market context",
            ),
        )


def test_interpret_returns_structured_result_from_matching_rule():
    result = InvestorSummaryRuleSet(
        rules=(StructuredFakeRule(),)
    ).interpret(make_event())

    assert result.summary == "Structured summary"
    assert result.explanation == Explanation(
        why_it_matters="Structured importance explanation",
        market_context="Structured market context",
    )
