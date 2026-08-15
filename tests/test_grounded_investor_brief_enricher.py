from unittest.mock import Mock

import pytest

from models.event import Event
from models.explanation import Explanation
from models.investor_brief import InvestorBrief
from models.portfolio_holding import PortfolioHolding
from models.portfolio_impact import PortfolioImpact
from models.source_document import SourceDocument
from models.source_evidence import SourceEvidence
from models.source_finding import SourceFinding
from models.source_grounded_brief import SourceGroundedBrief
from product.grounded_investor_brief_enricher import (
    GroundedInvestorBriefEnricher,
)


def make_brief(
    source: str = "SEC",
) -> InvestorBrief:
    event = Event(
        symbol="LQDA",
        source=source,
        title="Material company update",
        summary="Original event summary",
        published_at="2026-08-12",
        importance=8,
        sentiment="neutral",
        url="https://example.com/source",
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


def make_document() -> SourceDocument:
    return SourceDocument(
        source="SEC",
        source_url="https://example.com/source",
        title="Material company update",
        text=(
            "The company announced completion of "
            "a previously disclosed transaction."
        ),
    )


def make_grounded_brief() -> SourceGroundedBrief:
    return SourceGroundedBrief(
        findings=(
            SourceFinding(
                statement=(
                    "The company completed a previously "
                    "disclosed transaction."
                ),
                materiality=9,
                evidence=(
                    SourceEvidence(
                        source_url="https://example.com/source",
                        text=(
                            "The company announced completion of "
                            "a previously disclosed transaction."
                        ),
                    ),
                ),
            ),
        ),
    )


def test_enriches_brief_with_general_grounded_intelligence() -> None:
    document_provider = Mock()
    grounded_service = Mock()
    summary_builder = Mock()

    document = make_document()
    grounded_brief = make_grounded_brief()

    document_provider.build.return_value = document
    grounded_service.build.return_value = grounded_brief
    summary_builder.build.return_value = (
        "The company completed a previously disclosed transaction."
    )

    enricher = GroundedInvestorBriefEnricher(
        document_provider=document_provider,
        grounded_brief_service=grounded_service,
        summary_builder=summary_builder,
    )

    original = make_brief()
    enriched = enricher.enrich(original)

    assert enriched is not original
    assert enriched.summary == (
        "The company completed a previously disclosed transaction."
    )
    assert enriched.event is original.event

    document_provider.build.assert_called_once_with(
        original.event
    )
    grounded_service.build.assert_called_once_with(
        document
    )
    summary_builder.build.assert_called_once_with(
        grounded_brief
    )


def test_returns_original_brief_when_no_source_document_exists() -> None:
    document_provider = Mock()
    grounded_service = Mock()
    summary_builder = Mock()

    document_provider.build.return_value = None

    enricher = GroundedInvestorBriefEnricher(
        document_provider=document_provider,
        grounded_brief_service=grounded_service,
        summary_builder=summary_builder,
    )

    brief = make_brief(source="FDA")

    assert enricher.enrich(brief) is brief

    document_provider.build.assert_called_once_with(
        brief.event
    )
    grounded_service.build.assert_not_called()
    summary_builder.build.assert_not_called()


def test_returns_original_brief_when_grounded_service_returns_none() -> None:
    document_provider = Mock()
    grounded_service = Mock()
    summary_builder = Mock()

    document = make_document()

    document_provider.build.return_value = document
    grounded_service.build.return_value = None

    enricher = GroundedInvestorBriefEnricher(
        document_provider=document_provider,
        grounded_brief_service=grounded_service,
        summary_builder=summary_builder,
    )

    brief = make_brief()

    assert enricher.enrich(brief) is brief

    grounded_service.build.assert_called_once_with(
        document
    )
    summary_builder.build.assert_not_called()


def test_returns_original_brief_when_summary_is_blank() -> None:
    document_provider = Mock()
    grounded_service = Mock()
    summary_builder = Mock()

    document = make_document()
    grounded_brief = make_grounded_brief()

    document_provider.build.return_value = document
    grounded_service.build.return_value = grounded_brief
    summary_builder.build.return_value = "   "

    enricher = GroundedInvestorBriefEnricher(
        document_provider=document_provider,
        grounded_brief_service=grounded_service,
        summary_builder=summary_builder,
    )

    brief = make_brief()

    assert enricher.enrich(brief) is brief


def test_propagates_grounded_enrichment_failure_to_service_boundary() -> None:
    document_provider = Mock()
    grounded_service = Mock()
    summary_builder = Mock()

    document_provider.build.side_effect = RuntimeError(
        "source unavailable"
    )

    enricher = GroundedInvestorBriefEnricher(
        document_provider=document_provider,
        grounded_brief_service=grounded_service,
        summary_builder=summary_builder,
    )

    brief = make_brief()

    with pytest.raises(
        RuntimeError,
        match="source unavailable",
    ):
        enricher.enrich(brief)
