from models.event import Event
from models.explanation import Explanation
from models.investor_brief import InvestorBrief
from models.portfolio_holding import PortfolioHolding
from models.portfolio_impact import PortfolioImpact
from presentation.telegram_formatter import TelegramFormatter


def test_formatter_returns_human_readable_message():
    event = Event(
        symbol="AAPL",
        source="SEC",
        title="SEC Filing: 8-K",
        summary="Apple published a material filing.",
        published_at="2026-08-02T12:00:00+00:00",
        importance=9,
        sentiment="neutral",
        url="https://www.sec.gov/",
    )

    holding = PortfolioHolding(
        symbol="AAPL",
        quantity=10,
        average_cost=180.0,
    )

    impact = PortfolioImpact(
        holding=holding,
        event=event,
        matches_portfolio=True,
    )

    brief = InvestorBrief(
        event=event,
        ranking_position=1,
        portfolio_impact=impact,
        headline="Apple filed an 8-K",
        summary="Material filing detected.",
        explanation=Explanation(
            why_it_matters="Important corporate disclosure.",
            market_context="Could affect investor expectations.",
        ),
    )

    message = TelegramFormatter().format(brief)

    assert "AAPL" in message
    assert "Apple filed an 8-K" in message
    assert "Important corporate disclosure." in message
    assert "SEC" in message


def test_formatter_contains_required_investor_intelligence_sections():
    event = Event(
        symbol="LQDA",
        source="SEC",
        title="SEC Filing: 8-K",
        summary="Liquidia published a material SEC filing.",
        published_at="2026-08-02T12:00:00+00:00",
        importance=9,
        sentiment="neutral",
        url="https://www.sec.gov/example",
    )

    holding = PortfolioHolding(
        symbol="LQDA",
        quantity=7.99,
        average_cost=66.79,
    )

    impact = PortfolioImpact(
        holding=holding,
        event=event,
        matches_portfolio=True,
    )

    brief = InvestorBrief(
        event=event,
        ranking_position=1,
        portfolio_impact=impact,
        headline="דיווח מהותי חדש של LQDA",
        summary="Liquidia פרסמה דיווח מהותי חדש ל-SEC.",
        explanation=Explanation(
            why_it_matters="הדיווח עשוי לכלול מידע מהותי למשקיעים.",
            market_context="תגובת השוק תלויה בתוכן המלא של הדיווח.",
        ),
    )

    message = TelegramFormatter().format(brief)

    assert "דחיפות" in message
    assert "מה קרה" in message
    assert "למה זה חשוב" in message
    assert "השפעה על התיק" in message
    assert "מה לשקול" in message
    assert "מקור" in message
    assert "LQDA" in message
    assert event.url in message