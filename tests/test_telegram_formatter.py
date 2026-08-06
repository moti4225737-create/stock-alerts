from models.investor_intelligence_card import (
    EventCategory,
    ImportanceLevel,
    InvestorIntelligenceCard,
)
from presentation.telegram_formatter import TelegramFormatter


def make_card(
    source_url: str | None = "https://www.sec.gov/example",
    published_at: str = "2026-08-03T10:00:00+00:00",
) -> InvestorIntelligenceCard:
    return InvestorIntelligenceCard(
        importance_level=ImportanceLevel.CRITICAL,
        event_category=EventCategory.MATERIAL_FILING,
        title="\u05d3\u05d9\u05d5\u05d5\u05d7 \u05de\u05d4\u05d5\u05ea\u05d9 \u05d7\u05d3\u05e9",
        symbol="LQDA",
        summary=(
            "Liquidia \u05e4\u05e8\u05e1\u05de\u05d4 "
            "\u05d3\u05d9\u05d5\u05d5\u05d7 8-K \u05d7\u05d3\u05e9 \u05dc-SEC."
        ),
        why_it_matters=(
            "\u05d4\u05d3\u05d9\u05d5\u05d5\u05d7 \u05e2\u05e9\u05d5\u05d9 "
            "\u05dc\u05db\u05dc\u05d5\u05dc \u05de\u05d9\u05d3\u05e2 "
            "\u05de\u05d4\u05d5\u05ea\u05d9 \u05e9\u05d9\u05e9\u05e4\u05d9\u05e2 "
            "\u05e2\u05dc \u05e6\u05d9\u05e4\u05d9\u05d5\u05ea "
            "\u05d4\u05de\u05e9\u05e7\u05d9\u05e2\u05d9\u05dd."
        ),
        market_context="Must not appear.",
        portfolio_impact="Must not appear.",
        points_to_watch=("Must not appear.",),
        source="SEC",
        source_url=source_url,
        published_at=published_at,
    )


def test_formatter_renders_compact_intelligence_message() -> None:
    message = TelegramFormatter().format(make_card())

    assert "LQDA \u2014 \u05d3\u05d9\u05d5\u05d5\u05d7 \u05de\u05d4\u05d5\u05ea\u05d9 \u05d7\u05d3\u05e9" in message
    assert "\U0001f4a1 \u05dc\u05de\u05d4 \u05d6\u05d4 \u05d7\u05e9\u05d5\u05d1?" in message
    assert "\U0001f552 \u05e4\u05d5\u05e8\u05e1\u05dd:" in message
    assert "03/08/2026 10:00 UTC" in message
    assert "\U0001f517 \u05de\u05e7\u05d5\u05e8:" in message
    assert "SEC" in message
    assert "https://www.sec.gov/example" in message
    assert "Must not appear." not in message


def test_formatter_does_not_expose_internal_score_or_alarm_language() -> None:
    message = TelegramFormatter().format(make_card())

    assert "/10" not in message
    assert "Action Required" not in message


def test_formatter_omits_missing_source_url() -> None:
    message = TelegramFormatter().format(
        make_card(source_url=None)
    )

    assert "None" not in message
    assert "SEC" in message


def test_formatter_omits_artificial_midnight_time() -> None:
    message = TelegramFormatter().format(
        make_card(
            published_at="2026-08-03T00:00:00+00:00",
        )
    )

    assert "03/08/2026" in message
    assert "00:00" not in message
