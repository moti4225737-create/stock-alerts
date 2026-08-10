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


def test_service_builds_brief_from_discovered_verified_ranked_findings() -> None:
    document = SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="10-Q",
        text=(
            "Milestone delayed. "
            "Cash declined. "
            "Revenue increased."
        ),
    )

    candidates = (
        make_candidate("Revenue increased."),
        make_candidate("Milestone delayed."),
        make_candidate("Cash declined."),
    )

    discovery_service = Mock()
    discovery_service.discover.return_value = candidates

    materiality_evaluator = Mock()
    materiality_evaluator.evaluate.side_effect = (
        SourceFinding(
            statement="Revenue increased.",
            materiality=6,
            evidence=candidates[0].evidence,
        ),
        SourceFinding(
            statement="Milestone delayed.",
            materiality=10,
            evidence=candidates[1].evidence,
        ),
        SourceFinding(
            statement="Cash declined.",
            materiality=8,
            evidence=candidates[2].evidence,
        ),
    )

    finding_selector = Mock()
    finding_selector.select.return_value = (
        SourceFinding(
            statement="Milestone delayed.",
            materiality=10,
            evidence=candidates[1].evidence,
        ),
        SourceFinding(
            statement="Cash declined.",
            materiality=8,
            evidence=candidates[2].evidence,
        ),
    )

    service = SourceGroundedBriefService(
        discovery_service=discovery_service,
        materiality_evaluator=materiality_evaluator,
        finding_selector=finding_selector,
    )

    brief = service.build(document)

    assert [
        finding.statement
        for finding in brief.findings
    ] == [
        "Milestone delayed.",
        "Cash declined.",
    ]

    discovery_service.discover.assert_called_once_with(document)
    assert materiality_evaluator.evaluate.call_count == 3
    finding_selector.select.assert_called_once()


def test_service_returns_none_when_no_verified_candidates_exist() -> None:
    discovery_service = Mock()
    discovery_service.discover.return_value = ()

    service = SourceGroundedBriefService(
        discovery_service=discovery_service,
        materiality_evaluator=Mock(),
        finding_selector=Mock(),
    )

    document = SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="10-Q",
        text="Source text",
    )

    assert service.build(document) is None
