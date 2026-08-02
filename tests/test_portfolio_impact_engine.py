from engines.portfolio_impact_engine import PortfolioImpactEngine
from models.event import Event
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding
from models.portfolio_impact import PortfolioImpact


def test_portfolio_impact_engine_returns_matches_for_portfolio_symbols():
    holding = PortfolioHolding(symbol="AAPL", quantity=10, average_cost=150.0)
    portfolio = Portfolio([holding])

    event = Event(
        symbol="AAPL",
        source="SEC",
        title="Apple event",
        summary="Apple event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )

    engine = PortfolioImpactEngine()
    impacts = engine.analyze(portfolio, [event])

    assert impacts == [PortfolioImpact(holding=holding, event=event, matches_portfolio=True)]


def test_portfolio_impact_engine_ignores_events_not_in_portfolio():
    holding = PortfolioHolding(symbol="AAPL", quantity=10, average_cost=150.0)
    portfolio = Portfolio([holding])

    event = Event(
        symbol="MSFT",
        source="SEC",
        title="Microsoft event",
        summary="Microsoft event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )

    engine = PortfolioImpactEngine()
    impacts = engine.analyze(portfolio, [event])

    assert impacts == []


def test_portfolio_impact_engine_returns_multiple_matches_for_multiple_holdings():
    holding_one = PortfolioHolding(symbol="AAPL", quantity=10, average_cost=150.0)
    holding_two = PortfolioHolding(symbol="MSFT", quantity=5, average_cost=300.0)
    portfolio = Portfolio([holding_one, holding_two])

    event_one = Event(
        symbol="AAPL",
        source="SEC",
        title="Apple event",
        summary="Apple event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )
    event_two = Event(
        symbol="MSFT",
        source="SEC",
        title="Microsoft event",
        summary="Microsoft event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=7,
        sentiment="neutral",
    )

    engine = PortfolioImpactEngine()
    impacts = engine.analyze(portfolio, [event_one, event_two])

    assert impacts == [
        PortfolioImpact(holding=holding_one, event=event_one, matches_portfolio=True),
        PortfolioImpact(holding=holding_two, event=event_two, matches_portfolio=True),
    ]
