from engines.explanation_engine import ExplanationEngine
from engines.portfolio_intelligence_service import PortfolioIntelligenceService
from models.event import Event
from models.explanation import Explanation
from models.investor_rule_result import InvestorRuleResult
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding
from product.investor_summary_policy import InvestorSummaryPolicy


class FakeProvider:
    def __init__(self, events_by_symbol: dict[str, list[Event]] | None = None, failures: set[str] | None = None) -> None:
        self._events_by_symbol = events_by_symbol or {}
        self._failures = failures or set()

    def fetch_events(self, symbol: str) -> list[Event]:
        if symbol in self._failures:
            raise ValueError(f"provider failed for {symbol}")
        return list(self._events_by_symbol.get(symbol, []))


def test_build_briefs_ranks_and_filters_events_for_portfolio_symbols():
    aapl_event = Event(
        symbol="AAPL",
        source="SEC",
        title="SEC Filing: 10-Q",
        summary="Quarterly report",
        published_at="2026-08-01T10:00:00+00:00",
        importance=4,
        sentiment="neutral",
        url="https://example.com/aapl",
    )
    msft_event = Event(
        symbol="MSFT",
        source="SEC",
        title="SEC Filing: 8-K",
        summary="Material event",
        published_at="2026-08-01T09:00:00+00:00",
        importance=8,
        sentiment="neutral",
        url="https://example.com/msft",
    )

    holding_aapl = PortfolioHolding(symbol="AAPL", quantity=10, average_cost=150.0)
    holding_msft = PortfolioHolding(symbol="MSFT", quantity=5, average_cost=300.0)
    portfolio = Portfolio([holding_aapl, holding_msft])

    provider = FakeProvider(
        events_by_symbol={
            "AAPL": [aapl_event],
            "MSFT": [msft_event],
        }
    )

    service = PortfolioIntelligenceService()
    briefs, errors = service.build_briefs(portfolio, provider)

    assert errors == []
    assert len(briefs) == 2
    assert briefs[0].event == msft_event
    assert briefs[0].ranking_position == 1
    assert briefs[0].portfolio_impact.matches_portfolio is True
    msft_interpretation = InvestorSummaryPolicy().interpret(msft_event)
    assert briefs[0].summary == msft_interpretation.summary
    assert briefs[0].explanation == msft_interpretation.explanation

    assert briefs[1].event == aapl_event
    assert briefs[1].ranking_position == 2
    assert briefs[1].portfolio_impact.matches_portfolio is True
    aapl_interpretation = InvestorSummaryPolicy().interpret(aapl_event)
    assert briefs[1].summary == aapl_interpretation.summary
    assert briefs[1].explanation == aapl_interpretation.explanation


def test_build_briefs_reports_provider_failures_without_stopping_other_symbols():
    aapl_event = Event(
        symbol="AAPL",
        source="SEC",
        title="SEC Filing: 10-Q",
        summary="Quarterly report",
        published_at="2026-08-01T10:00:00+00:00",
        importance=4,
        sentiment="neutral",
        url="https://example.com/aapl",
    )

    holding_aapl = PortfolioHolding(symbol="AAPL", quantity=10, average_cost=150.0)
    holding_msft = PortfolioHolding(symbol="MSFT", quantity=5, average_cost=300.0)
    portfolio = Portfolio([holding_aapl, holding_msft])

    provider = FakeProvider(
        events_by_symbol={"AAPL": [aapl_event]},
        failures={"MSFT"},
    )

    service = PortfolioIntelligenceService()
    briefs, errors = service.build_briefs(portfolio, provider)

    assert len(briefs) == 1
    assert briefs[0].event == aapl_event
    assert errors == ["MSFT: provider failed for MSFT"]


def test_build_briefs_supports_empty_portfolios():
    provider = FakeProvider()
    service = PortfolioIntelligenceService()

    briefs, errors = service.build_briefs(Portfolio([]), provider)

    assert briefs == []
    assert errors == []


class FakeInvestorSummaryPolicy:
    def __init__(self, summary: str) -> None:
        self._summary = summary
        self.received_events: list[Event] = []

    def build(self, event: Event) -> str:
        self.received_events.append(event)
        return self._summary


def test_build_briefs_uses_investor_summary_policy():
    event = Event(
        symbol="LQDA",
        source="SEC",
        title="SEC Filing: 8-K",
        summary="Raw provider summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )
    portfolio = Portfolio(
        [
            PortfolioHolding(
                symbol="LQDA",
                quantity=7.99,
                average_cost=66.79,
            )
        ]
    )
    provider = FakeProvider(events_by_symbol={"LQDA": [event]})
    summary_policy = FakeInvestorSummaryPolicy(
        "החברה פרסמה דיווח מהותי חדש ל-SEC."
    )
    service = PortfolioIntelligenceService(
        investor_summary_policy=summary_policy,
    )

    briefs, errors = service.build_briefs(portfolio, provider)

    assert errors == []
    assert briefs[0].summary == (
        "החברה פרסמה דיווח מהותי חדש ל-SEC."
    )
    assert summary_policy.received_events == [event]

class StructuredInvestorSummaryPolicy:
    def __init__(self, result: InvestorRuleResult) -> None:
        self._result = result
        self.received_events: list[Event] = []

    def interpret(self, event: Event) -> InvestorRuleResult:
        self.received_events.append(event)
        return self._result


class FailingExplanationEngine:
    def explain(self, event: Event) -> Explanation:
        raise AssertionError(
            "ExplanationEngine must not be used when a structured "
            "rule interpretation is available"
        )


def test_build_briefs_uses_structured_rule_interpretation():
    event = Event(
        symbol="LQDA",
        source="SEC",
        title="SEC Filing: 8-K",
        summary="Entry into a Material Definitive Agreement",
        published_at="2026-08-05T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )
    portfolio = Portfolio(
        [
            PortfolioHolding(
                symbol="LQDA",
                quantity=7.99,
                average_cost=66.79,
            )
        ]
    )
    provider = FakeProvider(events_by_symbol={"LQDA": [event]})
    expected_result = InvestorRuleResult(
        summary="Structured investor summary",
        explanation=Explanation(
            why_it_matters="Structured importance explanation",
            market_context="Structured market context",
        ),
    )
    summary_policy = StructuredInvestorSummaryPolicy(expected_result)

    service = PortfolioIntelligenceService(
        investor_summary_policy=summary_policy,
        explanation_engine=FailingExplanationEngine(),
    )

    briefs, errors = service.build_briefs(portfolio, provider)

    assert errors == []
    assert briefs[0].summary == expected_result.summary
    assert briefs[0].explanation == expected_result.explanation
    assert summary_policy.received_events == [event]
