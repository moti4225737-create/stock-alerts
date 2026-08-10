from unittest.mock import Mock

from application.source_finding_discovery_service import (
    SourceFindingDiscoveryService,
)
from models.source_document import SourceDocument
from models.source_evidence import SourceEvidence
from models.source_finding_candidate import SourceFindingCandidate
from product.source_evidence_validator import SourceEvidenceValidator


def make_candidate(
    statement: str,
    evidence_text: str,
) -> SourceFindingCandidate:
    return SourceFindingCandidate(
        statement=statement,
        evidence=(
            SourceEvidence(
                source_url="https://www.sec.gov/example",
                text=evidence_text,
            ),
        ),
    )


def make_document() -> SourceDocument:
    return SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="10-Q",
        text=(
            "Revenue increased 18%. "
            "The pivotal milestone is expected in Q2 2027."
        ),
    )


def test_discovery_service_combines_valid_candidates() -> None:
    document = make_document()

    first = Mock()
    second = Mock()

    first.discover.return_value = (
        make_candidate(
            "Revenue increased 18%.",
            "Revenue increased 18%",
        ),
    )
    second.discover.return_value = (
        make_candidate(
            "The pivotal milestone is expected in Q2 2027.",
            "The pivotal milestone is expected in Q2 2027",
        ),
    )

    service = SourceFindingDiscoveryService(
        discoverers=(first, second),
        evidence_validator=SourceEvidenceValidator(),
    )

    candidates = service.discover(document)

    assert [
        candidate.statement
        for candidate in candidates
    ] == [
        "Revenue increased 18%.",
        "The pivotal milestone is expected in Q2 2027.",
    ]


def test_discovery_service_rejects_ungrounded_candidates() -> None:
    document = make_document()

    discoverer = Mock()
    discoverer.discover.return_value = (
        make_candidate(
            "Revenue increased 40%.",
            "Revenue increased 40%",
        ),
    )

    service = SourceFindingDiscoveryService(
        discoverers=(discoverer,),
        evidence_validator=SourceEvidenceValidator(),
    )

    assert service.discover(document) == ()
