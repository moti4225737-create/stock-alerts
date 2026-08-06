from application.investor_brief_enrichment_service import (
    InvestorBriefEnrichmentService,
)
from modules.sec_filing_client import SECFilingClient
from modules.sec_filing_extractor import SECFilingExtractor
from modules.sec_filing_parser import SECFilingParser
from modules.sec_signal_extractor import SECSignalExtractor
from product.sec_intelligence_summary_builder import (
    SECIntelligenceSummaryBuilder,
)
from product.sec_investor_brief_enricher import (
    SECInvestorBriefEnricher,
)


def build_default_investor_brief_enrichment_service(
    user_agent: str,
    timeout: int = 20,
) -> InvestorBriefEnrichmentService:
    client = SECFilingClient(
        user_agent=user_agent,
        timeout=timeout,
    )
    filing_extractor = SECFilingExtractor(
        client=client,
        parser=SECFilingParser(),
    )
    sec_enricher = SECInvestorBriefEnricher(
        filing_extractor=filing_extractor,
        signal_extractor=SECSignalExtractor(),
        summary_builder=SECIntelligenceSummaryBuilder(),
    )

    return InvestorBriefEnrichmentService(
        enrichers=(sec_enricher,),
    )
