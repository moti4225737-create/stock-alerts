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
            why_it_matters=(
                "The filing may affect investor expectations."
            ),
            market_context="The filing may change near-term investor expectations.",
        ),
    )


def test_builder_transforms_brief_into_notification_v1() -> None:
    message = TelegramIntelligenceMessageBuilder().build(
        make_brief()
    )

    assert isinstance(message, str)
    assert "\U0001f9ec LQDA" in message
    assert "SEC" in message
    assert "03/08/2026 10:00 UTC" in message
    assert "https://www.sec.gov/example" in message


def test_builder_places_business_title_before_technical_code() -> None:
    message = TelegramIntelligenceMessageBuilder().build(
        make_brief()
    )

    business_title = (
        "\u05d3\u05d9\u05d5\u05d5\u05d7 "
        "\u05de\u05d4\u05d5\u05ea\u05d9 "
        "\u05d7\u05d3\u05e9"
    )
    technical_code = "(SEC Form 8-K)"

    assert business_title in message
    assert technical_code in message
    assert message.index(business_title) < message.index(
        technical_code
    )


def test_builder_renders_supporting_intelligence_from_card() -> None:
    message = TelegramIntelligenceMessageBuilder().build(
        make_brief()
    )

    assert "The filing may change near-term investor expectations." in message
    assert "\U0001f4c8" in message
    assert "\U0001f3af" in message
    assert "\U0001f440" in message
