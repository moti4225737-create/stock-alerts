from application.investor_notification_service import InvestorNotificationService
from engines.portfolio_intelligence_service import PortfolioIntelligenceService
from models.event import Event
from models.investor_brief import InvestorBrief
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding


class FakeProvider:
    def fetch_events(self, symbol: str) -> list[Event]:
        return [
            Event(
                symbol=symbol,
                source="SEC",
                title=f"SEC Filing: {symbol}",
                summary="Material filing.",
                published_at="2026-08-03T10:00:00+00:00",
                importance=9,
                sentiment="neutral",
                url="https://www.sec.gov/example",
            )
        ]


def make_portfolio(symbols: list[str]) -> Portfolio:
    holdings = [
        PortfolioHolding(symbol=symbol, quantity=1.0, average_cost=10.0)
        for symbol in symbols
    ]
    return Portfolio(holdings)


def test_runtime_flow_converts_briefs_into_messages() -> None:
    portfolio = make_portfolio(["LQDA"])
    intelligence_service = PortfolioIntelligenceService()
    notification_service = InvestorNotificationService()

    briefs, errors = intelligence_service.build_briefs(portfolio, FakeProvider())
    messages = notification_service.generate_messages(briefs)

    assert errors == []
    assert len(briefs) == 1
    assert len(messages) == 1
    assert "LQDA" in messages[0]
    assert "SEC" in messages[0]
    assert isinstance(briefs[0], InvestorBrief)


def test_runtime_flow_returns_empty_tuple_when_no_briefs() -> None:
    intelligence_service = PortfolioIntelligenceService()
    notification_service = InvestorNotificationService()

    briefs, errors = intelligence_service.build_briefs(Portfolio([]), FakeProvider())
    messages = notification_service.generate_messages(briefs)

    assert errors == []
    assert briefs == []
    assert messages == ()


def test_runtime_flow_preserves_message_order() -> None:
    portfolio = make_portfolio(["AAPL", "MSFT"])
    intelligence_service = PortfolioIntelligenceService()
    notification_service = InvestorNotificationService()

    briefs, errors = intelligence_service.build_briefs(portfolio, FakeProvider())
    messages = notification_service.generate_messages(briefs)

    assert errors == []
    assert len(messages) == 2
    assert "AAPL" in messages[0]
    assert "MSFT" in messages[1]
