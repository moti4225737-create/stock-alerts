from models.investor_brief import InvestorBrief
from models.investor_intelligence_card import InvestorIntelligenceCard
from product.event_category_policy import EventCategoryPolicy
from product.importance_policy import ImportancePolicy
from product.investor_intelligence_card_assembler import (
    InvestorIntelligenceCardAssembler,
)


class InvestorIntelligenceCardOrchestrator:
    def __init__(
        self,
        importance_policy: ImportancePolicy | None = None,
        event_category_policy: EventCategoryPolicy | None = None,
        assembler: InvestorIntelligenceCardAssembler | None = None,
    ) -> None:
        self._importance_policy = importance_policy or ImportancePolicy()
        self._event_category_policy = (
            event_category_policy or EventCategoryPolicy()
        )
        self._assembler = assembler or InvestorIntelligenceCardAssembler()

    def build(
        self,
        brief: InvestorBrief,
        portfolio_impact: str,
        points_to_watch: tuple[str, ...],
    ) -> InvestorIntelligenceCard:
        event = brief.event

        return self._assembler.assemble(
            brief=brief,
            importance_level=self._importance_policy.classify(event),
            event_category=self._event_category_policy.classify(event),
            portfolio_impact=portfolio_impact,
            points_to_watch=points_to_watch,
        )