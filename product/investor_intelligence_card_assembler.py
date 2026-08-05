from models.investor_brief import InvestorBrief
from models.investor_intelligence_card import (
    EventCategory,
    ImportanceLevel,
    InvestorIntelligenceCard,
)


class InvestorIntelligenceCardAssembler:
    def assemble(
        self,
        brief: InvestorBrief,
        importance_level: ImportanceLevel,
        event_category: EventCategory,
        portfolio_impact: str,
        points_to_watch: tuple[str, ...],
    ) -> InvestorIntelligenceCard:
        event = brief.event

        return InvestorIntelligenceCard(
            importance_level=importance_level,
            event_category=event_category,
            title=brief.headline,
            symbol=event.symbol,
            summary=brief.summary,
            why_it_matters=brief.explanation.why_it_matters,
            market_context=brief.explanation.market_context,
            portfolio_impact=portfolio_impact,
            points_to_watch=points_to_watch,
            source=event.source,
            source_url=event.url,
            published_at=event.published_at,
        )