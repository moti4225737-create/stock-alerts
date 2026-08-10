from collections.abc import Iterable
from typing import Protocol

from models.source_document import SourceDocument
from models.source_finding_candidate import SourceFindingCandidate


class SourceFindingDiscoverer(Protocol):
    def discover(
        self,
        document: SourceDocument,
    ) -> tuple[SourceFindingCandidate, ...]:
        ...


class EvidenceValidator(Protocol):
    def is_valid(
        self,
        document: SourceDocument,
        finding: SourceFindingCandidate,
    ) -> bool:
        ...


class SourceFindingDiscoveryService:
    def __init__(
        self,
        discoverers: Iterable[SourceFindingDiscoverer],
        evidence_validator: EvidenceValidator,
    ) -> None:
        self._discoverers = tuple(discoverers)
        self._evidence_validator = evidence_validator

    def discover(
        self,
        document: SourceDocument,
    ) -> tuple[SourceFindingCandidate, ...]:
        candidates: list[SourceFindingCandidate] = []

        for discoverer in self._discoverers:
            for candidate in discoverer.discover(document):
                if self._evidence_validator.is_valid(
                    document=document,
                    finding=candidate,
                ):
                    candidates.append(candidate)

        return tuple(candidates)
