from dataclasses import FrozenInstanceError

import pytest

from models.investor_intelligence_card import (
    EventCategory,
    ImportanceLevel,
    InvestorIntelligenceCard,
)


def test_investor_intelligence_card_contains_product_contract_fields():
    card = InvestorIntelligenceCard(
        importance_level=ImportanceLevel.HIGH,
        event_category=EventCategory.MATERIAL_FILING,
        title="Material SEC filing",
        symbol="LQDA",
        summary="Liquidia published a new material SEC filing.",
        why_it_matters=(
            "The filing may contain information that changes "
            "investor expectations."
        ),
        market_context=(
            "The filing should be evaluated against the company's "
            "financial position and market expectations."
        ),
        portfolio_impact=(
            "LQDA is held in the portfolio, so the disclosure "
            "is directly relevant."
        ),
        points_to_watch=(
            "Review the filing details.",
            "Monitor the market response.",
        ),
        source="SEC",
        source_url="https://www.sec.gov/example",
        published_at="2026-08-02T12:00:00+00:00",
    )

    assert card.importance_level is ImportanceLevel.HIGH
    assert card.event_category is EventCategory.MATERIAL_FILING
    assert card.title == "Material SEC filing"
    assert card.symbol == "LQDA"
    assert card.summary == "Liquidia published a new material SEC filing."
    assert card.why_it_matters.startswith("The filing may contain")
    assert card.market_context.startswith(
        "The filing should be evaluated"
    )
    assert card.portfolio_impact.startswith("LQDA is held")
    assert card.points_to_watch == (
        "Review the filing details.",
        "Monitor the market response.",
    )
    assert card.source == "SEC"
    assert card.source_url == "https://www.sec.gov/example"
    assert card.published_at == "2026-08-02T12:00:00+00:00"


def test_investor_intelligence_card_is_immutable():
    card = InvestorIntelligenceCard(
        importance_level=ImportanceLevel.MODERATE,
        event_category=EventCategory.CORPORATE_DISCLOSURE,
        title="Corporate disclosure",
        symbol="AAPL",
        summary="Apple published a corporate disclosure.",
        why_it_matters="The disclosure may affect investor expectations.",
        market_context="Monitor the broader corporate context.",
        portfolio_impact="AAPL is held in the portfolio.",
        points_to_watch=("Review the disclosure.",),
        source="SEC",
        source_url=None,
        published_at="2026-08-02T12:00:00+00:00",
    )

    with pytest.raises(FrozenInstanceError):
        card.summary = "Changed summary"
