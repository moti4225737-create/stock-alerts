from models.event import Event
from models.explanation import Explanation
from models.investor_brief import InvestorBrief
from models.investor_intelligence_card import (
    EventCategory,
    ImportanceLevel,
    InvestorIntelligenceCard,
)
from models.portfolio_holding import PortfolioHolding
from models.portfolio_impact import PortfolioImpact
from product.investor_intelligence_card_assembler import (
    InvestorIntelligenceCardAssembler,
)


def test_assembler_builds_product_contract_from_prepared_intelligence():
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

    impact = PortfolioImpact(
        holding=holding,
        event=event,
        matches_portfolio=True,
    )

    brief = InvestorBrief(
        event=event,
        ranking_position=1,
        portfolio_impact=impact,
        headline="Material SEC filing",
        summary=event.summary,
        explanation=Explanation(
            why_it_matters="The filing may affect investor expectations.",
            market_context="Monitor the market response.",
        ),
    )

    card = InvestorIntelligenceCardAssembler().assemble(
        brief=brief,
        importance_level=ImportanceLevel.HIGH,
        event_category=EventCategory.MATERIAL_FILING,
        portfolio_impact=(
            "LQDA is held in the portfolio, so the disclosure "
            "is directly relevant."
        ),
        points_to_watch=(
            "Review the filing details.",
            "Monitor the market response.",
        ),
    )

    assert isinstance(card, InvestorIntelligenceCard)
    assert card.importance_level is ImportanceLevel.HIGH
    assert card.event_category is EventCategory.MATERIAL_FILING
    assert card.title == brief.headline
    assert card.symbol == event.symbol
    assert card.summary == brief.summary
    assert card.why_it_matters == brief.explanation.why_it_matters
    assert card.portfolio_impact.startswith("LQDA is held")
    assert card.points_to_watch == (
        "Review the filing details.",
        "Monitor the market response.",
    )
    assert card.source == event.source
    assert card.source_url == event.url
    assert card.published_at == event.published_at


def test_assembler_does_not_expose_internal_ranking_position():
    event = Event(
        symbol="AAPL",
        source="SEC",
        title="Corporate disclosure",
        summary="Apple published a corporate disclosure.",
        published_at="2026-08-03T11:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )

    holding = PortfolioHolding(
        symbol="AAPL",
        quantity=10,
        average_cost=180.0,
    )

    brief = InvestorBrief(
        event=event,
        ranking_position=3,
        portfolio_impact=PortfolioImpact(
            holding=holding,
            event=event,
            matches_portfolio=True,
        ),
        headline="Corporate disclosure",
        summary=event.summary,
        explanation=Explanation(
            why_it_matters="The disclosure may affect expectations.",
            market_context="Monitor subsequent developments.",
        ),
    )

    card = InvestorIntelligenceCardAssembler().assemble(
        brief=brief,
        importance_level=ImportanceLevel.MODERATE,
        event_category=EventCategory.CORPORATE_DISCLOSURE,
        portfolio_impact="AAPL is held in the portfolio.",
        points_to_watch=("Review the disclosure.",),
    )

    assert not hasattr(card, "ranking_position")