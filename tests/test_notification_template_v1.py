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
        summary="\u05d4\u05d4\u05db\u05e0\u05e1\u05d5\u05ea \u05d1\u05e8\u05d1\u05e2\u05d5\u05df \u05d4\u05e1\u05ea\u05db\u05de\u05d5 \u05d1-13.4 \u05de\u05d9\u05dc\u05d9\u05d5\u05df \u05d3\u05d5\u05dc\u05e8.",
        why_it_matters="\u05d4\u05d7\u05d1\u05e8\u05d4 \u05de\u05e6\u05d9\u05d2\u05d4 \u05e9\u05d9\u05e4\u05d5\u05e8 \u05d1\u05d4\u05db\u05e0\u05e1\u05d5\u05ea, \u05d0\u05da \u05e2\u05d3\u05d9\u05d9\u05df \u05e8\u05d5\u05e9\u05de\u05ea \u05d4\u05e4\u05e1\u05d3.",
        market_context="\u05d4\u05ea\u05d5\u05e6\u05d0\u05d5\u05ea \u05e2\u05e9\u05d5\u05d9\u05d5\u05ea \u05dc\u05e9\u05e0\u05d5\u05ea \u05d0\u05ea \u05e6\u05d9\u05e4\u05d9\u05d5\u05ea \u05d4\u05e9\u05d5\u05e7 \u05dc\u05d2\u05d1\u05d9 \u05d4\u05d7\u05d1\u05e8\u05d4.",
        portfolio_impact="OABI \u05de\u05d5\u05d7\u05d6\u05e7\u05ea \u05d1\u05ea\u05d9\u05e7 \u05d5\u05dc\u05db\u05df \u05d4\u05d3\u05d5\u05d7 \u05e8\u05dc\u05d5\u05d5\u05e0\u05d8\u05d9 \u05d9\u05e9\u05d9\u05e8\u05d5\u05ea.",
        points_to_watch=(
            "\u05e2\u05e7\u05d5\u05d1 \u05d0\u05d7\u05e8 \u05d4\u05e0\u05d7\u05d9\u05d5\u05ea \u05d4\u05d4\u05e0\u05d4\u05dc\u05d4.",
        ),
        source="SEC",
        source_url="https://www.sec.gov/example",
        published_at="2026-08-06T00:00:00+00:00",
    )


def test_explainer_places_business_meaning_before_technical_code() -> None:
    explainer = ProfessionalTermExplainer()

    assert explainer.explain("SEC Filing: 10-Q") == (
        "\u05d3\u05d5\u05d7 \u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 \u05d7\u05d3\u05e9\n"
        "(SEC Form 10-Q)"
    )


def test_formatter_renders_notification_template_v1() -> None:
    message = TelegramFormatter().format(
        make_quarterly_card()
    )

    assert "\U0001f9ec OABI" in message
    assert "\u05d3\u05d5\u05d7 \u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 \u05d7\u05d3\u05e9" in message
    assert "(SEC Form 10-Q)" in message
    assert "\U0001f4cb \u05de\u05d4 \u05e7\u05e8\u05d4?" in message
    assert "\U0001f4a1 \u05dc\u05de\u05d4 \u05d6\u05d4 \u05d7\u05e9\u05d5\u05d1?" in message
    assert "\U0001f4c8 \u05d4\u05e7\u05e9\u05e8 \u05e9\u05d5\u05e7" in message
    assert "\U0001f3af \u05de\u05d4 \u05d4\u05e7\u05e9\u05e8 \u05d0\u05dc\u05d9\u05d9?" in message
    assert "\U0001f440 \u05de\u05d4 \u05dc\u05e2\u05e7\u05d5\u05d1?" in message
    assert "06/08/2026" in message
    assert "00:00" not in message
    assert "SEC" in message
    assert "https://www.sec.gov/example" in message
