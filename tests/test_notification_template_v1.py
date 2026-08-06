from models.investor_intelligence_card import (
    EventCategory,
    ImportanceLevel,
    InvestorIntelligenceCard,
)
from presentation.professional_term_explainer import (
    ProfessionalTermExplainer,
)
from presentation.telegram_formatter import TelegramFormatter


def make_quarterly_card() -> InvestorIntelligenceCard:
    return InvestorIntelligenceCard(
        importance_level=ImportanceLevel.HIGH,
        event_category=EventCategory.CORPORATE_DISCLOSURE,
        title="SEC Filing: 10-Q",
        symbol="OABI",
        summary=(
            "\u05d4\u05d4\u05db\u05e0\u05e1\u05d5\u05ea "
            "\u05d1\u05e8\u05d1\u05e2\u05d5\u05df "
            "\u05d4\u05e1\u05ea\u05db\u05de\u05d5 "
            "\u05d1-13.4 \u05de\u05d9\u05dc\u05d9\u05d5\u05df "
            "\u05d3\u05d5\u05dc\u05e8."
        ),
        why_it_matters=(
            "\u05d4\u05d7\u05d1\u05e8\u05d4 "
            "\u05de\u05e6\u05d9\u05d2\u05d4 "
            "\u05e9\u05d9\u05e4\u05d5\u05e8 "
            "\u05d1\u05d4\u05db\u05e0\u05e1\u05d5\u05ea, "
            "\u05d0\u05da "
            "\u05e2\u05d3\u05d9\u05d9\u05df "
            "\u05e8\u05d5\u05e9\u05de\u05ea "
            "\u05d4\u05e4\u05e1\u05d3."
        ),
        market_context="MUST NOT APPEAR",
        portfolio_impact="MUST NOT APPEAR",
        points_to_watch=("MUST NOT APPEAR",),
        source="SEC",
        source_url="https://www.sec.gov/example",
        published_at="2026-08-06T00:00:00+00:00",
    )


def test_explainer_places_business_meaning_before_technical_code() -> None:
    explainer = ProfessionalTermExplainer()

    assert explainer.explain("SEC Filing: 10-Q") == (
        "\u05d3\u05d5\u05d7 "
        "\u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 "
        "\u05d7\u05d3\u05e9\n"
        "(SEC Form 10-Q)"
    )


def test_formatter_renders_notification_template_v1() -> None:
    message = TelegramFormatter().format(
        make_quarterly_card()
    )

    assert message == (
        "\U0001f9ec OABI\n\n"
        "\u05d3\u05d5\u05d7 "
        "\u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 "
        "\u05d7\u05d3\u05e9\n"
        "(SEC Form 10-Q)\n\n"
        "\U0001f4cb \u05de\u05d4 \u05e7\u05e8\u05d4?\n"
        "\u05d4\u05d4\u05db\u05e0\u05e1\u05d5\u05ea "
        "\u05d1\u05e8\u05d1\u05e2\u05d5\u05df "
        "\u05d4\u05e1\u05ea\u05db\u05de\u05d5 "
        "\u05d1-13.4 \u05de\u05d9\u05dc\u05d9\u05d5\u05df "
        "\u05d3\u05d5\u05dc\u05e8.\n\n"
        "\U0001f4a1 \u05d4\u05e2\u05e8\u05db\u05ea "
        "\u05d6\u05e7\u05d9\u05e3\n"
        "\u05d4\u05d7\u05d1\u05e8\u05d4 "
        "\u05de\u05e6\u05d9\u05d2\u05d4 "
        "\u05e9\u05d9\u05e4\u05d5\u05e8 "
        "\u05d1\u05d4\u05db\u05e0\u05e1\u05d5\u05ea, "
        "\u05d0\u05da "
        "\u05e2\u05d3\u05d9\u05d9\u05df "
        "\u05e8\u05d5\u05e9\u05de\u05ea "
        "\u05d4\u05e4\u05e1\u05d3.\n\n"
        "\U0001f552 \u05e4\u05d5\u05e8\u05e1\u05dd\n"
        "06/08/2026\n\n"
        "\U0001f517 \u05de\u05e7\u05d5\u05e8\n"
        "SEC\n"
        "https://www.sec.gov/example"
    )

    assert "MUST NOT APPEAR" not in message
