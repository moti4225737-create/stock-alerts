from unittest.mock import Mock

from application.source_grounded_brief_service import (
    SourceGroundedBriefService,
)
from models.source_document import SourceDocument
from models.source_evidence import SourceEvidence
from models.source_finding import SourceFinding
from models.source_finding_candidate import SourceFindingCandidate


def make_candidate(
    statement: str,
) -> SourceFindingCandidate:
    return SourceFindingCandidate(
        statement=statement,
        evidence=(
            SourceEvidence(
                source_url="https://www.sec.gov/example",
                text=statement,
            ),
        ),
    )


def test_service_filters_unresolved_findings_before_selection() -> None:
    document = SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="8-K",
        text=(
            "Material development. "
            "Ambiguous development."
        ),
    )

    assessed_candidate = make_candidate(
        "Material development."
    )
    unresolved_candidate = make_candidate(
        "Ambiguous development."
    )

    assessed_finding = SourceFinding(
        statement=assessed_candidate.statement,
        materiality=9,
        evidence=assessed_candidate.evidence,
    )

    discovery_service = Mock()
    discovery_service.discover.return_value = (
        assessed_candidate,
        unresolved_candidate,
    )

    materiality_evaluator = Mock()
    materiality_evaluator.evaluate.side_effect = (
        assessed_finding,
        None,
    )

    finding_selector = Mock()
    finding_selector.select.return_value = (
        assessed_finding,
    )

    service = SourceGroundedBriefService(
        discovery_service=discovery_service,
        materiality_evaluator=materiality_evaluator,
        finding_selector=finding_selector,
    )

    service.build(document)

    finding_selector.select.assert_called_once_with(
        (assessed_finding,)
    )
