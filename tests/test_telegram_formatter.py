from models.investor_intelligence_card import (
    EventCategory,
    ImportanceLevel,
    InvestorIntelligenceCard,
)
from presentation.telegram_formatter import TelegramFormatter


def make_card(
    source_url: str | None = "https://www.sec.gov/example",
) -> InvestorIntelligenceCard:
    return InvestorIntelligenceCard(
        importance_level=ImportanceLevel.CRITICAL,
        event_category=EventCategory.MATERIAL_FILING,
        title="דיווח מהותי חדש",
        symbol="LQDA",
        summary="Liquidia פרסמה דיווח 8-K חדש ל-SEC.",
        why_it_matters=(
            "הדיווח עשוי לכלול מידע מהותי שישפיע "
            "על ציפיות המשקיעים."
        ),
        market_context=(
            "\u05d9\u05e9 "
            "\u05dc\u05d1\u05d7\u05d5\u05df "
            "\u05d0\u05ea "
            "\u05ea\u05d5\u05db\u05df "
            "\u05d4\u05d3\u05d9\u05d5\u05d5\u05d7 "
            "\u05d5\u05d0\u05ea "
            "\u05d4\u05e9\u05e4\u05e2\u05ea\u05d5 "
            "\u05d4\u05d0\u05e4\u05e9\u05e8\u05d9\u05ea "
            "\u05e2\u05dc "
            "\u05e4\u05e2\u05d9\u05dc\u05d5\u05ea "
            "\u05d4\u05d7\u05d1\u05e8\u05d4 "
            "\u05d5\u05d4\u05ea\u05d7\u05d6\u05d9\u05ea."
        ),
        portfolio_impact=(
            "LQDA מוחזקת בתיק ולכן האירוע רלוונטי ישירות."
        ),
        points_to_watch=(
            "לבדוק את תוכן הדיווח.",
            "לעקוב אחר תגובת השוק.",
        ),
        source="SEC",
        source_url=source_url,
        published_at="2026-08-03T10:00:00+00:00",
    )


def test_formatter_renders_investor_intelligence_card():
    message = TelegramFormatter().format(make_card())

    assert "🧬 LQDA" in message
    assert "🔴 קריטית" in message
    assert "📌 אירוע: דיווח מהותי" in message
    assert "📰 מה קרה?" in message
    assert "💡 למה זה חשוב?" in message
    assert "📈 ההשפעה על התיק שלך" in message
    assert "👀 מה כדאי לעקוב?" in message
    assert "• לבדוק את תוכן הדיווח." in message
    assert "• לעקוב אחר תגובת השוק." in message
    assert "🕒 פורסם:" in message
    assert "03/08/2026 10:00 UTC" in message
    assert "🔗 מקור:" in message
    assert "SEC" in message
    assert "https://www.sec.gov/example" in message


def test_formatter_does_not_expose_internal_score_or_alarm_language():
    message = TelegramFormatter().format(make_card())

    assert "/10" not in message
    assert "דחיפות" not in message
    assert "Action Required" not in message


def test_formatter_omits_missing_source_url():
    message = TelegramFormatter().format(make_card(source_url=None))

    assert "None" not in message
    assert "🔗 מקור:" in message
    assert "SEC" in message
