from unittest.mock import Mock

from application.source_grounded_brief_service import (
    SourceGroundedBriefService,
)
from models.source_document import SourceDocument
from models.source_evidence import SourceEvidence
from models.source_finding import SourceFinding
from models.source_finding_candidate import SourceFindingCandidate


def make_candidate() -> SourceFindingCandidate:
    statement = "Milestone delayed."

    return SourceFindingCandidate(
        statement=statement,
        evidence=(
            SourceEvidence(
                source_url="https://www.sec.gov/example",
                text=statement,
            ),
        ),
    )


def test_service_passes_source_document_to_materiality_evaluator() -> None:
    document = SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="8-K",
        text="Milestone delayed.",
    )

    candidate = make_candidate()

    discovery_service = Mock()
    discovery_service.discover.return_value = (
        candidate,
    )

    finding = SourceFinding(
        statement=candidate.statement,
        materiality=9,
        evidence=candidate.evidence,
    )

    materiality_evaluator = Mock()
    materiality_evaluator.evaluate.return_value = finding

    finding_selector = Mock()
    finding_selector.select.return_value = (
        finding,
    )

    service = SourceGroundedBriefService(
        discovery_service=discovery_service,
        materiality_evaluator=materiality_evaluator,
        finding_selector=finding_selector,
    )

    service.build(document)

    materiality_evaluator.evaluate.assert_called_once_with(
        candidate,
        document,
    )
