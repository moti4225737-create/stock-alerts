from typing import Protocol

from application.investor_brief_enrichment_service import (
    InvestorBriefEnrichmentService,
)
from application.source_finding_discovery_service import (
    SourceFindingDiscoveryService,
)
from application.source_grounded_brief_service import (
    SourceGroundedBriefService,
)
from models.semantic_finding_proposal import SemanticFindingProposal
from models.significance_assessment import SignificanceAssessment
from models.source_document import SourceDocument
from models.source_finding_candidate import SourceFindingCandidate
from modules.sec_filing_client import SECFilingClient
from modules.sec_filing_extractor import SECFilingExtractor
from modules.sec_filing_parser import SECFilingParser
from modules.sec_signal_extractor import SECSignalExtractor
from product.grounded_investor_brief_enricher import (
    GroundedInvestorBriefEnricher,
)
from product.sec_deterministic_finding_discoverer import (
    SECDeterministicFindingDiscoverer,
)
from product.sec_source_document_provider import (
    SECSourceDocumentProvider,
)
from product.semantic_finding_discoverer import (
    SemanticFindingDiscoverer,
)
from product.source_evidence_validator import (
    SourceEvidenceValidator,
)
from product.source_finding_selector import (
    SourceFindingSelector,
)
from product.source_grounded_summary_builder import (
    SourceGroundedSummaryBuilder,
)
from product.source_materiality_evaluator import (
    SourceMaterialityEvaluator,
)


class SemanticAnalyzer(Protocol):
    def analyze(
        self,
        document: SourceDocument,
    ) -> tuple[SemanticFindingProposal, ...]:
        ...


class SignificanceAssessor(Protocol):
    def assess(
        self,
        candidate: SourceFindingCandidate,
        document: SourceDocument,
    ) -> SignificanceAssessment:
        ...


def build_default_investor_brief_enrichment_service(
    user_agent: str,
    semantic_analyzer: SemanticAnalyzer,
    significance_assessor: SignificanceAssessor,
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

    document_provider = SECSourceDocumentProvider(
        filing_extractor=filing_extractor,
    )

    deterministic_discoverer = SECDeterministicFindingDiscoverer(
        signal_extractor=SECSignalExtractor(),
    )

    semantic_discoverer = SemanticFindingDiscoverer(
        analyzer=semantic_analyzer,
    )

    discovery_service = SourceFindingDiscoveryService(
        discoverers=(
            deterministic_discoverer,
            semantic_discoverer,
        ),
        evidence_validator=SourceEvidenceValidator(),
    )

    grounded_brief_service = SourceGroundedBriefService(
        discovery_service=discovery_service,
        materiality_evaluator=SourceMaterialityEvaluator(
            assessor=significance_assessor,
        ),
        finding_selector=SourceFindingSelector(),
    )

    grounded_enricher = GroundedInvestorBriefEnricher(
        document_provider=document_provider,
        grounded_brief_service=grounded_brief_service,
        summary_builder=SourceGroundedSummaryBuilder(),
    )

    return InvestorBriefEnrichmentService(
        enrichers=(grounded_enricher,),
    )
