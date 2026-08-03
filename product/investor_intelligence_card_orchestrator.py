from models.investor_brief import InvestorBrief
from models.investor_intelligence_card import InvestorIntelligenceCard
from product.event_category_policy import EventCategoryPolicy
from product.importance_policy import ImportancePolicy
from product.investor_intelligence_card_assembler import (
    InvestorIntelligenceCardAssembler,
)
from product.points_to_watch_policy import PointsToWatchPolicy
from product.portfolio_impact_narrative_policy import (
    PortfolioImpactNarrativePolicy,
)


class InvestorIntelligenceCardOrchestrator:
    def __init__(
        self,
        importance_policy: ImportancePolicy | None = None,
        event_category_policy: EventCategoryPolicy | None = None,
        portfolio_impact_narrative_policy: (
            PortfolioImpactNarrativePolicy | None
        ) = None,
        points_to_watch_policy: PointsToWatchPolicy | None = None,
        assembler: InvestorIntelligenceCardAssembler | None = None,
    ) -> None:
        self._importance_policy = importance_policy or ImportancePolicy()
        self._event_category_policy = (
            event_category_policy or EventCategoryPolicy()
        )
        self._portfolio_impact_narrative_policy = (
            portfolio_impact_narrative_policy
            or PortfolioImpactNarrativePolicy()
        )
        self._points_to_watch_policy = (
            points_to_watch_policy or PointsToWatchPolicy()
        )
        self._assembler = assembler or InvestorIntelligenceCardAssembler()

    def build(
        self,
        brief: InvestorBrief,
    ) -> InvestorIntelligenceCard:
        event = brief.event

        return self._assembler.assemble(
            brief=brief,
            importance_level=self._importance_policy.classify(event),
            event_category=self._event_category_policy.classify(event),
            portfolio_impact=(
                self._portfolio_impact_narrative_policy.describe(
                    brief.portfolio_impact
                )
            ),
            points_to_watch=self._points_to_watch_policy.build(event),
        )