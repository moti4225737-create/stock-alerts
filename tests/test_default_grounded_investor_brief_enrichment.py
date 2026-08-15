from unittest.mock import Mock

from application.default_investor_brief_enrichment import (
    build_default_investor_brief_enrichment_service,
)
from application.investor_brief_enrichment_service import (
    InvestorBriefEnrichmentService,
)
from product.grounded_investor_brief_enricher import (
    GroundedInvestorBriefEnricher,
)


def test_builds_default_grounded_enrichment_pipeline() -> None:
    semantic_analyzer = Mock()
    significance_assessor = Mock()

    service = build_default_investor_brief_enrichment_service(
        user_agent="Stock Sentinel test@example.com",
        timeout=15,
        semantic_analyzer=semantic_analyzer,
        significance_assessor=significance_assessor,
    )

    assert isinstance(
        service,
        InvestorBriefEnrichmentService,
    )

    assert len(service._enrichers) == 1

    assert isinstance(
        service._enrichers[0],
        GroundedInvestorBriefEnricher,
    )
