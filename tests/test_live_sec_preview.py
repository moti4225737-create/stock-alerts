from apps.live_sec_preview import build_live_briefs, build_portfolio
from engines.explanation_engine import ExplanationEngine
from models.event import Event
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding


class FakeProvider:
    def __init__(self, events_by_symbol: dict[str, list[Event]] | None = None) -> None:
        self._events_by_symbol = events_by_symbol or {}

    def fetch_events(self, symbol: str) -> list[Event]:
        return list(self._events_by_symbol.get(symbol, []))


def test_build_portfolio_creates_holdings_from_symbols():
    portfolio = build_portfolio(["AAPL", "MSFT"])

    assert isinstance(portfolio, Portfolio)
    assert [holding.symbol for holding in portfolio.holdings] == ["AAPL", "MSFT"]
    assert all(isinstance(holding, PortfolioHolding) for holding in portfolio.holdings)


def test_build_live_briefs_uses_provider_and_explanation_engine():
    event = Event(
        symbol="AAPL",
        source="SEC",
        title="SEC Filing: 8-K",
        summary="Material event",
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
        url="https://example.com/aapl",
    )

    briefs, errors = build_live_briefs(["AAPL"], FakeProvider({"AAPL": [event]}))

    assert errors == []
    assert len(briefs) == 1
    assert briefs[0].event == event
    assert briefs[0].explanation == ExplanationEngine().explain(event)
