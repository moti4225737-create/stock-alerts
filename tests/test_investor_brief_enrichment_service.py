from unittest.mock import Mock

from application.investor_brief_enrichment_service import (
    InvestorBriefEnrichmentService,
)
from models.event import Event
from models.explanation import Explanation
from models.investor_brief import InvestorBrief
from models.portfolio_holding import PortfolioHolding
from models.portfolio_impact import PortfolioImpact


def make_brief(
    symbol: str,
    source: str,
) -> InvestorBrief:
    event = Event(
        symbol=symbol,
        source=source,
        title="Test event",
        summary="Basic summary",
        published_at="2026-08-06",
        importance=8,
        sentiment="neutral",
        url="https://example.com",
    )
    holding = PortfolioHolding(
        symbol=symbol,
        quantity=1,
        average_cost=0,
    )

    return InvestorBrief(
        event=event,
        ranking_position=1,
        portfolio_impact=PortfolioImpact(
            holding=holding,
            event=event,
            matches_portfolio=True,
        ),
        headline=event.title,
        summary=event.summary,
        explanation=Explanation(
            why_it_matters="Basic explanation",
            market_context="Basic context",
        ),
    )


def test_enriches_briefs_in_original_order() -> None:
    first = make_brief("LQDA", "SEC")
    second = make_brief("ACTU", "FDA")

    enricher = Mock()
    enriched_first = Mock()
    enriched_second = Mock()
    enricher.enrich.side_effect = [
        enriched_first,
        enriched_second,
    ]

    service = InvestorBriefEnrichmentService(
        enrichers=(enricher,),
    )

    result = service.enrich_all([first, second])

    assert result == (
        enriched_first,
        enriched_second,
    )
    assert enricher.enrich.call_args_list[0].args == (first,)
    assert enricher.enrich.call_args_list[1].args == (second,)


def test_returns_original_brief_when_enricher_fails() -> None:
    brief = make_brief("LQDA", "SEC")

    enricher = Mock()
    enricher.enrich.side_effect = RuntimeError(
        "Enrichment failed"
    )

    service = InvestorBriefEnrichmentService(
        enrichers=(enricher,),
    )

    assert service.enrich_all([brief]) == (brief,)


def test_returns_empty_tuple_without_briefs() -> None:
    service = InvestorBriefEnrichmentService(
        enrichers=(),
    )

    assert service.enrich_all([]) == ()
