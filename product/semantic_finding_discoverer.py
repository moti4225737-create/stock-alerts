from typing import Protocol

from models.semantic_finding_proposal import SemanticFindingProposal
from models.source_document import SourceDocument
from models.source_evidence import SourceEvidence
from models.source_finding_candidate import SourceFindingCandidate


class SemanticAnalyzer(Protocol):
    def analyze(
        self,
        document: SourceDocument,
    ) -> tuple[SemanticFindingProposal, ...]:
        ...


class SemanticFindingDiscoverer:
    def __init__(
        self,
        analyzer: SemanticAnalyzer,
    ) -> None:
        self._analyzer = analyzer

    def discover(
        self,
        document: SourceDocument,
    ) -> tuple[SourceFindingCandidate, ...]:
        proposals = self._analyzer.analyze(document)

        return tuple(
            SourceFindingCandidate(
                statement=proposal.statement,
                evidence=(
                    SourceEvidence(
                        source_url=document.source_url,
                        text=proposal.evidence_text,
                        locator=proposal.locator,
                    ),
                ),
            )
            for proposal in proposals
        )
