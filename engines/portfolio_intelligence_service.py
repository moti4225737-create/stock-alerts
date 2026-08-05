from engines.explanation_engine import ExplanationEngine
from engines.portfolio_impact_engine import PortfolioImpactEngine
from engines.signal_ranking_engine import SignalRankingEngine
from models.event import Event
from models.investor_brief import InvestorBrief
from models.portfolio import Portfolio
from modules.data_provider import DataProvider
from product.investor_summary_policy import InvestorSummaryPolicy


class PortfolioIntelligenceService:
    def __init__(
        self,
        signal_ranking_engine: SignalRankingEngine | None = None,
        portfolio_impact_engine: PortfolioImpactEngine | None = None,
        explanation_engine: ExplanationEngine | None = None,
        investor_summary_policy: InvestorSummaryPolicy | None = None,
    ) -> None:
        self._signal_ranking_engine = (
            signal_ranking_engine or SignalRankingEngine()
        )
        self._portfolio_impact_engine = (
            portfolio_impact_engine or PortfolioImpactEngine()
        )
        self._explanation_engine = (
            explanation_engine or ExplanationEngine()
        )
        self._investor_summary_policy = (
            investor_summary_policy or InvestorSummaryPolicy()
        )

    def build_briefs(
        self,
        portfolio: Portfolio,
        provider: DataProvider,
    ) -> tuple[list[InvestorBrief], list[str]]:
        if not portfolio.holdings:
            return [], []

        events: list[Event] = []
        errors: list[str] = []

        for holding in portfolio.holdings:
            try:
                fetched_events = provider.fetch_events(holding.symbol)
            except Exception as exc:  # pragma: no cover - defensive handling for provider failures
                errors.append(f"{holding.symbol}: {exc}")
                continue

            events.extend(fetched_events)

        ranked_events = self._signal_ranking_engine.rank(events)
        impacts = self._portfolio_impact_engine.analyze(
            portfolio,
            ranked_events,
        )

        briefs: list[InvestorBrief] = []
        for index, impact in enumerate(impacts, start=1):
            event = impact.event
            interpret = getattr(
                self._investor_summary_policy,
                "interpret",
                None,
            )

            if callable(interpret):
                try:
                    interpretation = interpret(event)
                except LookupError:
                    summary = self._investor_summary_policy.build(event)
                    explanation = self._explanation_engine.explain(event)
                else:
                    summary = interpretation.summary
                    explanation = interpretation.explanation
            else:
                summary = self._investor_summary_policy.build(event)
                explanation = self._explanation_engine.explain(event)

            briefs.append(
                InvestorBrief(
                    event=event,
                    ranking_position=index,
                    portfolio_impact=impact,
                    headline=event.title,
                    summary=summary,
                    explanation=explanation,
                )
            )

        return briefs, errors