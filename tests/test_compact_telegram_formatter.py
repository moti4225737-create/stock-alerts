from models.investor_intelligence_card import (
    EventCategory,
    ImportanceLevel,
    InvestorIntelligenceCard,
)
from presentation.telegram_formatter import TelegramFormatter


def test_compact_message() -> None:
    card = InvestorIntelligenceCard(
        importance_level=ImportanceLevel.HIGH,
        event_category=EventCategory.CORPORATE_DISCLOSURE,
        title="\U0001f4ca LQDA \u05e4\u05e8\u05e1\u05de\u05d4 \u05d3\u05d5\u05d7 \u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 \u05d7\u05d3\u05e9",
        symbol="LQDA",
        summary="\u05d4\u05d7\u05d1\u05e8\u05d4 \u05e4\u05e8\u05e1\u05de\u05d4 \u05d0\u05ea \u05d4\u05d3\u05d5\u05d7 \u05d4\u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 \u05e9\u05dc\u05d4 \u05dc-SEC.",
        why_it_matters="\u05ea\u05d5\u05e6\u05d0\u05d5\u05ea \u05d4\u05d3\u05d5\u05d7 \u05e2\u05e9\u05d5\u05d9\u05d5\u05ea \u05dc\u05d4\u05e9\u05e4\u05d9\u05e2 \u05e2\u05dc \u05d4\u05e2\u05e8\u05db\u05ea \u05d4\u05e9\u05d5\u05d5\u05d9 \u05d5\u05e6\u05d9\u05e4\u05d9\u05d5\u05ea \u05d4\u05de\u05e9\u05e7\u05d9\u05e2\u05d9\u05dd.",
        market_context="\u05d4\u05e9\u05d5\u05e7 \u05e2\u05e9\u05d5\u05d9 \u05dc\u05ea\u05de\u05d7\u05e8 \u05de\u05d7\u05d3\u05e9 \u05d0\u05ea \u05e6\u05d9\u05e4\u05d9\u05d5\u05ea \u05d4\u05e6\u05de\u05d9\u05d7\u05d4.",
        portfolio_impact="LQDA \u05de\u05d5\u05d7\u05d6\u05e7\u05ea \u05d1\u05ea\u05d9\u05e7 \u05d5\u05dc\u05db\u05df \u05d4\u05d0\u05d9\u05e8\u05d5\u05e2 \u05e8\u05dc\u05d5\u05d5\u05e0\u05d8\u05d9 \u05d9\u05e9\u05d9\u05e8\u05d5\u05ea.",
        points_to_watch=(
            "\u05e2\u05e7\u05d5\u05d1 \u05d0\u05d7\u05e8 \u05d4\u05e0\u05d7\u05d9\u05d5\u05ea \u05d4\u05d4\u05e0\u05d4\u05dc\u05d4.",
        ),
        source="SEC",
        source_url="https://www.sec.gov/example",
        published_at="2026-08-05T10:00:00+00:00",
    )

    message = TelegramFormatter().format(card)

    assert "\U0001f9ec LQDA" in message
    assert "\U0001f4cb \u05de\u05d4 \u05e7\u05e8\u05d4?" in message
    assert "\U0001f4a1 \u05dc\u05de\u05d4 \u05d6\u05d4 \u05d7\u05e9\u05d5\u05d1?" in message
    assert "\U0001f4c8 \u05d4\u05e7\u05e9\u05e8 \u05e9\u05d5\u05e7" in message
    assert "\U0001f3af \u05de\u05d4 \u05d4\u05e7\u05e9\u05e8 \u05d0\u05dc\u05d9\u05d9?" in message
    assert "\U0001f440 \u05de\u05d4 \u05dc\u05e2\u05e7\u05d5\u05d1?" in message
    assert "\U0001f552 \u05e4\u05d5\u05e8\u05e1\u05dd" in message
    assert "05/08/2026 10:00 UTC" in message
    assert "\U0001f517 \u05de\u05e7\u05d5\u05e8" in message
    assert "https://www.sec.gov/example" in message
