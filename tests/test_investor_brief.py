from models.event import Event
from models.explanation import Explanation
from models.investor_brief import InvestorBrief
from models.portfolio_impact import PortfolioImpact
from models.portfolio_holding import PortfolioHolding


def test_investor_brief_contains_expected_domain_fields():
    event = Event(
        symbol="AAPL",
        source="SEC",
        title="Apple event",
        summary="Apple event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )
    holding = PortfolioHolding(symbol="AAPL", quantity=10, average_cost=150.0)
    impact = PortfolioImpact(holding=holding, event=event, matches_portfolio=True)

    brief = InvestorBrief(
        event=event,
        ranking_position=1,
        portfolio_impact=impact,
        headline="Apple event is important",
        summary="Apple event summary",
        explanation=Explanation(
            why_it_matters="This event may be relevant to market participants and should be monitored.",
            market_context="The broader market impact will depend on how the news is interpreted over time.",
        ),
    )

    assert brief.event == event
    assert brief.ranking_position == 1
    assert brief.portfolio_impact == impact
    assert brief.headline == "Apple event is important"
    assert brief.summary == "Apple event summary"
