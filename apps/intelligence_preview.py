import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from engines.explanation_engine import ExplanationEngine
from engines.portfolio_impact_engine import PortfolioImpactEngine
from engines.signal_ranking_engine import SignalRankingEngine
from models.event import Event
from models.investor_brief import InvestorBrief
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding


def build_preview_briefs(
    portfolio: Portfolio,
    events: list[Event],
    signal_ranking_engine: SignalRankingEngine | None = None,
    portfolio_impact_engine: PortfolioImpactEngine | None = None,
) -> list[InvestorBrief]:
    ranking_engine = signal_ranking_engine or SignalRankingEngine()
    impact_engine = portfolio_impact_engine or PortfolioImpactEngine()

    ranked_events = ranking_engine.rank(events)
    impacts = impact_engine.analyze(portfolio, ranked_events)

    explanation_engine = ExplanationEngine()
    briefs: list[InvestorBrief] = []
    for index, impact in enumerate(impacts, start=1):
        briefing = InvestorBrief(
            event=impact.event,
            ranking_position=index,
            portfolio_impact=impact,
            headline=impact.event.title,
            summary=impact.event.summary,
            explanation=explanation_engine.explain(impact.event),
        )
        briefs.append(briefing)

    return briefs


def print_preview(briefs: list[InvestorBrief]) -> None:
    for brief in briefs:
        print(
            f"#{brief.ranking_position} | {brief.event.symbol} | {brief.headline} | {brief.summary} | portfolio match: {'yes' if brief.portfolio_impact.matches_portfolio else 'no'}"
        )


def main() -> None:
    holding = PortfolioHolding(symbol="AAPL", quantity=10, average_cost=150.0)
    portfolio = Portfolio([holding])

    events = [
        Event(
            symbol="AAPL",
            source="SEC",
            title="Apple earnings update",
            summary="Apple earnings summary",
            published_at="2026-08-01T10:00:00+00:00",
            importance=8,
            sentiment="neutral",
        ),
        Event(
            symbol="MSFT",
            source="SEC",
            title="Microsoft headline",
            summary="Microsoft summary",
            published_at="2026-08-01T11:00:00+00:00",
            importance=9,
            sentiment="neutral",
        ),
        Event(
            symbol="AAPL",
            source="SEC",
            title="Apple product launch",
            summary="Apple product summary",
            published_at="2026-08-01T09:00:00+00:00",
            importance=7,
            sentiment="neutral",
        ),
    ]

    briefs = build_preview_briefs(portfolio, events)
    print_preview(briefs)


if __name__ == "__main__":
    main()
