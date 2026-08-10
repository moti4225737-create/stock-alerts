from typing import Protocol

from models.source_document import SourceDocument
from models.source_finding import SourceFinding
from models.source_finding_candidate import SourceFindingCandidate
from models.source_grounded_brief import SourceGroundedBrief


class DiscoveryService(Protocol):
    def discover(
        self,
        document: SourceDocument,
    ) -> tuple[SourceFindingCandidate, ...]:
        ...


class MaterialityEvaluator(Protocol):
    def evaluate(
        self,
        candidate: SourceFindingCandidate,
    ) -> SourceFinding:
        ...


class FindingSelector(Protocol):
    def select(
        self,
        findings: tuple[SourceFinding, ...],
    ) -> tuple[SourceFinding, ...]:
        ...


class SourceGroundedBriefService:
    def __init__(
        self,
        discovery_service: DiscoveryService,
        materiality_evaluator: MaterialityEvaluator,
        finding_selector: FindingSelector,
    ) -> None:
        self._discovery_service = discovery_service
        self._materiality_evaluator = materiality_evaluator
        self._finding_selector = finding_selector

    def build(
        self,
        document: SourceDocument,
    ) -> SourceGroundedBrief | None:
        candidates = self._discovery_service.discover(document)

        if not candidates:
            return None

        findings = tuple(
            self._materiality_evaluator.evaluate(candidate)
            for candidate in candidates
        )

        selected = self._finding_selector.select(findings)

        if not selected:
            return None

        return SourceGroundedBrief(
            findings=selected,
        )
