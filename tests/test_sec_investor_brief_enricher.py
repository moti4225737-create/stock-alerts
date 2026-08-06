from unittest.mock import Mock

from models.event import Event
from models.explanation import Explanation
from models.investor_brief import InvestorBrief
from models.portfolio_holding import PortfolioHolding
from models.portfolio_impact import PortfolioImpact
from product.sec_investor_brief_enricher import (
    SECInvestorBriefEnricher,
)


def make_brief(
    source: str = "SEC",
    url: str | None = "https://www.sec.gov/example",
) -> InvestorBrief:
    event = Event(
        symbol="LQDA",
        source=source,
        title="SEC Filing: 10-Q",
        summary="Quarterly report",
        published_at="2026-08-05",
        importance=8,
        sentiment="neutral",
        url=url,
    )
    holding = PortfolioHolding(
        symbol="LQDA",
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
        summary="Basic summary",
        explanation=Explanation(
            why_it_matters="Basic explanation",
            market_context="Basic context",
        ),
    )


def test_enriches_sec_brief_with_document_intelligence() -> None:
    extractor = Mock()
    signal_extractor = Mock()
    summary_builder = Mock()

    extractor.extract.return_value = "Filing text"
    signal_extractor.extract.return_value = {
        "revenue": "increased 18%",
    }
    summary_builder.build.return_value = (
        "Revenue intelligence summary"
    )

    enricher = SECInvestorBriefEnricher(
        filing_extractor=extractor,
        signal_extractor=signal_extractor,
        summary_builder=summary_builder,
    )

    original = make_brief()
    enriched = enricher.enrich(original)

    assert enriched is not original
    assert enriched.summary == "Revenue intelligence summary"
    assert enriched.event is original.event
    extractor.extract.assert_called_once_with(
        "https://www.sec.gov/example"
    )
    signal_extractor.extract.assert_called_once_with(
        "Filing text"
    )


def test_returns_non_sec_brief_unchanged() -> None:
    enricher = SECInvestorBriefEnricher(
        filing_extractor=Mock(),
        signal_extractor=Mock(),
        summary_builder=Mock(),
    )
    brief = make_brief(source="FDA")

    assert enricher.enrich(brief) is brief


def test_returns_original_brief_when_enrichment_fails() -> None:
    extractor = Mock()
    extractor.extract.side_effect = RuntimeError(
        "SEC unavailable"
    )
    brief = make_brief()

    enricher = SECInvestorBriefEnricher(
        filing_extractor=extractor,
        signal_extractor=Mock(),
        summary_builder=Mock(),
    )

    assert enricher.enrich(brief) is brief
