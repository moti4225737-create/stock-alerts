from models.event import Event
from models.portfolio_holding import PortfolioHolding
from models.portfolio_impact import PortfolioImpact
from product.portfolio_impact_narrative_policy import (
    PortfolioImpactNarrativePolicy,
)


def make_impact(matches_portfolio: bool) -> PortfolioImpact:
    event = Event(
        symbol="LQDA",
        source="SEC",
        title="SEC Filing: 8-K",
        summary="Liquidia published a material filing.",
        published_at="2026-08-03T10:00:00+00:00",
        importance=9,
        sentiment="neutral",
    )

    holding = PortfolioHolding(
        symbol="LQDA",
        quantity=7.99,
        average_cost=66.79,
    )

    return PortfolioImpact(
        holding=holding,
        event=event,
        matches_portfolio=matches_portfolio,
    )


def test_matching_holding_produces_direct_portfolio_relevance():
    narrative = PortfolioImpactNarrativePolicy().describe(
        make_impact(matches_portfolio=True)
    )

    assert narrative == (
        "LQDA מוחזקת בתיק ולכן האירוע רלוונטי ישירות."
    )


def test_non_matching_holding_avoids_false_direct_relevance():
    narrative = PortfolioImpactNarrativePolicy().describe(
        make_impact(matches_portfolio=False)
    )

    assert narrative == (
        "לא נמצאה השפעה ישירה על אחת ההחזקות בתיק."
    )