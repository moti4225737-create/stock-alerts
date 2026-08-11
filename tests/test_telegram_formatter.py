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
        title="SEC Filing: 8-K",
        symbol="LQDA",
        summary=(
            "Liquidia published a material SEC filing "
            "with new information for investors."
        ),
        why_it_matters=(
            "The filing may change investor expectations "
            "about the company."
        ),
        market_context=(
            "The market may reassess the company as the "
            "new information is absorbed."
        ),
        portfolio_impact=(
            "The event is directly relevant because LQDA "
            "is held in the portfolio."
        ),
        points_to_watch=(
            "Watch for additional company clarification.",
            "Watch the market response to the filing.",
        ),
        source="SEC",
        source_url=source_url,
        published_at=published_at,
    )


def test_formatter_renders_current_event_first_with_supporting_intelligence() -> None:
    message = TelegramFormatter().format(make_card())

    assert "\U0001f9ec LQDA" in message
    assert (
        "\u05d3\u05d9\u05d5\u05d5\u05d7 "
        "\u05de\u05d4\u05d5\u05ea\u05d9 "
        "\u05d7\u05d3\u05e9"
    ) in message
    assert "(SEC Form 8-K)" in message

    assert "\U0001f4cb \u05de\u05d4 \u05e7\u05e8\u05d4?" in message
    assert (
        "Liquidia published a material SEC filing "
        "with new information for investors."
    ) in message

    assert "\U0001f4a1 \u05dc\u05de\u05d4 \u05d6\u05d4 \u05d7\u05e9\u05d5\u05d1?" in message
    assert (
        "The filing may change investor expectations "
        "about the company."
    ) in message

    assert "\U0001f4c8 \u05d4\u05e7\u05e9\u05e8 \u05e9\u05d5\u05e7" in message
    assert (
        "The market may reassess the company as the "
        "new information is absorbed."
    ) in message

    assert "\U0001f3af \u05de\u05d4 \u05d4\u05e7\u05e9\u05e8 \u05d0\u05dc\u05d9\u05d9?" in message
    assert (
        "The event is directly relevant because LQDA "
        "is held in the portfolio."
    ) in message

    assert "\U0001f440 \u05de\u05d4 \u05dc\u05e2\u05e7\u05d5\u05d1?" in message
    assert "Watch for additional company clarification." in message
    assert "Watch the market response to the filing." in message

    assert "03/08/2026 10:00 UTC" in message
    assert "SEC" in message
    assert "https://www.sec.gov/example" in message

    current_event_position = message.index(
        "\U0001f4cb \u05de\u05d4 \u05e7\u05e8\u05d4?"
    )
    why_position = message.index(
        "\U0001f4a1 \u05dc\u05de\u05d4 \u05d6\u05d4 \u05d7\u05e9\u05d5\u05d1?"
    )
    portfolio_position = message.index(
        "\U0001f3af \u05de\u05d4 \u05d4\u05e7\u05e9\u05e8 \u05d0\u05dc\u05d9\u05d9?"
    )

    assert current_event_position < why_position
    assert current_event_position < portfolio_position


def test_formatter_does_not_expose_internal_language() -> None:
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


def test_formatter_omits_points_section_when_all_points_are_blank() -> None:
    card = make_card()
    card = InvestorIntelligenceCard(
        importance_level=card.importance_level,
        event_category=card.event_category,
        title=card.title,
        symbol=card.symbol,
        summary=card.summary,
        why_it_matters=card.why_it_matters,
        market_context=card.market_context,
        portfolio_impact=card.portfolio_impact,
        points_to_watch=("", "   "),
        source=card.source,
        source_url=card.source_url,
        published_at=card.published_at,
    )

    message = TelegramFormatter().format(card)

    assert "\U0001f440 \u05de\u05d4 \u05dc\u05e2\u05e7\u05d5\u05d1?" not in message
