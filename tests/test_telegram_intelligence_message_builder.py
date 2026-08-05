from models.event import Event
from models.explanation import Explanation
from models.investor_brief import InvestorBrief
from models.portfolio_holding import PortfolioHolding
from models.portfolio_impact import PortfolioImpact
from presentation.telegram_intelligence_message_builder import (
    TelegramIntelligenceMessageBuilder,
)


def make_brief() -> InvestorBrief:
    event = Event(
        symbol="LQDA",
        source="SEC",
        title="SEC Filing: 8-K",
        summary="Liquidia published a material SEC filing.",
        published_at="2026-08-03T10:00:00+00:00",
        importance=9,
        sentiment="neutral",
        url="https://www.sec.gov/example",
    )

    holding = PortfolioHolding(
        symbol="LQDA",
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
        headline=event.title,
        summary=event.summary,
        explanation=Explanation(
            why_it_matters="The filing may affect investor expectations.",
            market_context="Monitor the market response.",
        ),
    )


def test_builder_transforms_brief_into_telegram_message():
    message = TelegramIntelligenceMessageBuilder().build(make_brief())

    assert isinstance(message, str)
    assert "LQDA" in message
    assert "SEC" in message
    assert "🔴 קריטית" in message


def test_builder_explains_professional_term_in_message():
    message = TelegramIntelligenceMessageBuilder().build(make_brief())

    assert "Form 8-K" in message
    assert "דיווח מיידי על אירוע מהותי בחברה" in message

def test_builder_includes_market_context_in_message():
    message = TelegramIntelligenceMessageBuilder().build(make_brief())

    assert (
        "\U0001f50e "
        "\u05de\u05d4 "
        "\u05d4\u05d4\u05e7\u05e9\u05e8 "
        "\u05dc\u05d4\u05e2\u05e8\u05db\u05ea "
        "\u05d4\u05d0\u05d9\u05e8\u05d5\u05e2?"
    ) in message
    assert "Monitor the market response." in message
