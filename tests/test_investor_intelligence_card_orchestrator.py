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
from product.investor_intelligence_card_orchestrator import (
    InvestorIntelligenceCardOrchestrator,
)


def make_brief() -> InvestorBrief:
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

    return InvestorBrief(
        event=event,
        ranking_position=1,
        portfolio_impact=PortfolioImpact(
            holding=holding,
            event=event,
            matches_portfolio=True,
        ),
        headline="Material SEC filing",
        summary=event.summary,
        explanation=Explanation(
            why_it_matters="The filing may affect investor expectations.",
            market_context="Monitor the market response.",
        ),
    )


def test_orchestrator_builds_investor_intelligence_card():
    brief = make_brief()

    card = InvestorIntelligenceCardOrchestrator().build(
        brief=brief,
        portfolio_impact="LQDA is held in the portfolio.",
        points_to_watch=("Review the filing.",),
    )

    assert card.importance_level is ImportanceLevel.CRITICAL
    assert card.event_category is EventCategory.MATERIAL_FILING
    assert card.title == "Material SEC filing"
    assert card.symbol == "LQDA"
    assert card.source == "SEC"


def test_orchestrator_coordinates_injected_dependencies():
    brief = make_brief()

    class StubImportancePolicy:
        def classify(self, event: Event) -> ImportanceLevel:
            assert event is brief.event
            return ImportanceLevel.HIGH

    class StubEventCategoryPolicy:
        def classify(self, event: Event) -> EventCategory:
            assert event is brief.event
            return EventCategory.CORPORATE_DISCLOSURE

    class RecordingAssembler:
        def __init__(self) -> None:
            self.received_arguments = None

        def assemble(
            self,
            brief: InvestorBrief,
            importance_level: ImportanceLevel,
            event_category: EventCategory,
            portfolio_impact: str,
            points_to_watch: tuple[str, ...],
        ) -> InvestorIntelligenceCard:
            self.received_arguments = {
                "brief": brief,
                "importance_level": importance_level,
                "event_category": event_category,
                "portfolio_impact": portfolio_impact,
                "points_to_watch": points_to_watch,
            }

            return InvestorIntelligenceCard(
                importance_level=importance_level,
                event_category=event_category,
                title=brief.headline,
                symbol=brief.event.symbol,
                summary=brief.summary,
                why_it_matters=brief.explanation.why_it_matters,
                portfolio_impact=portfolio_impact,
                points_to_watch=points_to_watch,
                source=brief.event.source,
                source_url=brief.event.url,
                published_at=brief.event.published_at,
            )

    assembler = RecordingAssembler()

    card = InvestorIntelligenceCardOrchestrator(
        importance_policy=StubImportancePolicy(),
        event_category_policy=StubEventCategoryPolicy(),
        assembler=assembler,
    ).build(
        brief=brief,
        portfolio_impact="Direct portfolio relevance.",
        points_to_watch=("Review the filing.",),
    )

    assert assembler.received_arguments == {
        "brief": brief,
        "importance_level": ImportanceLevel.HIGH,
        "event_category": EventCategory.CORPORATE_DISCLOSURE,
        "portfolio_impact": "Direct portfolio relevance.",
        "points_to_watch": ("Review the filing.",),
    }
    assert card.importance_level is ImportanceLevel.HIGH
    assert card.event_category is EventCategory.CORPORATE_DISCLOSURE