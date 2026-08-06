from application.default_investor_brief_enrichment import (
    build_default_investor_brief_enrichment_service,
)
from application.investor_brief_enrichment_service import (
    InvestorBriefEnrichmentService,
)
from product.sec_investor_brief_enricher import (
    SECInvestorBriefEnricher,
)


def test_builds_default_sec_enrichment_pipeline() -> None:
    service = build_default_investor_brief_enrichment_service(
        user_agent="Stock Sentinel test@example.com",
        timeout=15,
    )

    assert isinstance(
        service,
        InvestorBriefEnrichmentService,
    )
    assert len(service._enrichers) == 1
    assert isinstance(
        service._enrichers[0],
        SECInvestorBriefEnricher,
    )
