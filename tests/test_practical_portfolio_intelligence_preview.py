from apps.intelligence_preview import build_preview_briefs, print_preview
from engines.portfolio_impact_engine import PortfolioImpactEngine
from engines.signal_ranking_engine import SignalRankingEngine
from models.event import Event
from models.investor_brief import InvestorBrief
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding


def test_build_preview_briefs_uses_ranking_and_portfolio_matches():
    holding = PortfolioHolding(symbol="AAPL", quantity=10, average_cost=150.0)
    portfolio = Portfolio([holding])

    low_importance = Event(
        symbol="AAPL",
        source="SEC",
        title="Low importance event",
        summary="Low importance summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=3,
        sentiment="neutral",
    )
    high_importance = Event(
        symbol="AAPL",
        source="SEC",
        title="High importance event",
        summary="High importance summary",
        published_at="2026-08-01T09:00:00+00:00",
        importance=9,
        sentiment="neutral",
    )
    unrelated = Event(
        symbol="MSFT",
        source="SEC",
        title="Unrelated event",
        summary="Unrelated summary",
        published_at="2026-08-01T11:00:00+00:00",
        importance=10,
        sentiment="neutral",
    )

    briefs = build_preview_briefs(
        portfolio=portfolio,
        events=[low_importance, high_importance, unrelated],
        signal_ranking_engine=SignalRankingEngine(),
        portfolio_impact_engine=PortfolioImpactEngine(),
    )

    assert len(briefs) == 2
    assert briefs[0].ranking_position == 1
    assert briefs[0].event == high_importance
    assert briefs[0].portfolio_impact.matches_portfolio is True
    assert briefs[1].ranking_position == 2
    assert briefs[1].event == low_importance
    assert briefs[1].portfolio_impact.matches_portfolio is True
    assert all(isinstance(brief, InvestorBrief) for brief in briefs)


def test_print_preview_outputs_expected_lines(capsys):
    holding = PortfolioHolding(symbol="AAPL", quantity=10, average_cost=150.0)
    portfolio = Portfolio([holding])

    event = Event(
        symbol="AAPL",
        source="SEC",
        title="Apple event",
        summary="Apple event summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )

    briefs = build_preview_briefs(
        portfolio=portfolio,
        events=[event],
        signal_ranking_engine=SignalRankingEngine(),
        portfolio_impact_engine=PortfolioImpactEngine(),
    )

    print_preview(briefs)

    captured = capsys.readouterr().out
    assert "#1" in captured
    assert "AAPL" in captured
    assert "Apple event" in captured
    assert "Apple event summary" in captured
    assert "portfolio match: yes" in captured.lower()
