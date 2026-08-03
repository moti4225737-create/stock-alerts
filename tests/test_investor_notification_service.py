from application.investor_notification_service import InvestorNotificationService
from models.event import Event
from models.explanation import Explanation
from models.investor_brief import InvestorBrief
from models.portfolio_holding import PortfolioHolding
from models.portfolio_impact import PortfolioImpact


class FakeBuilder:
    def __init__(self) -> None:
        self.calls: list[InvestorBrief] = []

    def build(self, brief: InvestorBrief) -> str:
        self.calls.append(brief)
        return f"message:{brief.headline}"


def make_brief(symbol: str, headline: str) -> InvestorBrief:
    event = Event(
        symbol=symbol,
        source="SEC",
        title=headline,
        summary="Material filing.",
        published_at="2026-08-03T10:00:00+00:00",
        importance=9,
        sentiment="neutral",
        url="https://www.sec.gov/example",
    )

    holding = PortfolioHolding(
        symbol=symbol,
        quantity=7.99,
        average_cost=66.79,
    )

    return InvestorBrief(
        event=event,
        ranking_position=1,
        portfolio_impact=PortfolioImpact(
            holding=holding,
            event=event,
            matches_portfolio=True,
        ),
        headline=headline,
        summary=event.summary,
        explanation=Explanation(
            why_it_matters="The filing may affect investor expectations.",
            market_context="Monitor the market response.",
        ),
    )


def test_returns_empty_tuple_when_no_briefs() -> None:
    service = InvestorNotificationService()

    assert service.generate_messages([]) == ()


def test_formats_single_brief_using_builder() -> None:
    brief = make_brief("LQDA", "SEC Filing")
    builder = FakeBuilder()
    service = InvestorNotificationService(telegram_builder=builder)

    messages = service.generate_messages([brief])

    assert messages == ("message:SEC Filing",)
    assert builder.calls == [brief]


def test_formats_multiple_briefs_in_order() -> None:
    first = make_brief("AAPL", "First notice")
    second = make_brief("MSFT", "Second notice")
    builder = FakeBuilder()
    service = InvestorNotificationService(telegram_builder=builder)

    messages = service.generate_messages([first, second])

    assert messages == ("message:First notice", "message:Second notice")
    assert builder.calls == [first, second]