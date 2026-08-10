from unittest.mock import Mock

from models.semantic_finding_proposal import SemanticFindingProposal
from models.source_document import SourceDocument
from models.source_finding_candidate import SourceFindingCandidate
from product.semantic_finding_discoverer import (
    SemanticFindingDiscoverer,
)


def make_document() -> SourceDocument:
    return SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="10-Q",
        text="The pivotal milestone was delayed.",
    )


def test_semantic_discoverer_converts_structured_proposals_to_candidates() -> None:
    analyzer = Mock()
    analyzer.analyze.return_value = (
        SemanticFindingProposal(
            statement="The pivotal milestone was delayed.",
            evidence_text="The pivotal milestone was delayed.",
            locator="Item 2",
        ),
    )

    discoverer = SemanticFindingDiscoverer(
        analyzer=analyzer,
    )

    document = make_document()
    candidates = discoverer.discover(document)

    assert len(candidates) == 1
    assert isinstance(
        candidates[0],
        SourceFindingCandidate,
    )
    assert candidates[0].statement == (
        "The pivotal milestone was delayed."
    )
    assert candidates[0].evidence[0].source_url == (
        document.source_url
    )
    assert candidates[0].evidence[0].text == (
        "The pivotal milestone was delayed."
    )
    assert candidates[0].evidence[0].locator == "Item 2"

    analyzer.analyze.assert_called_once_with(document)


def test_semantic_discoverer_returns_empty_when_analyzer_finds_nothing() -> None:
    analyzer = Mock()
    analyzer.analyze.return_value = ()

    discoverer = SemanticFindingDiscoverer(
        analyzer=analyzer,
    )

    assert discoverer.discover(make_document()) == ()
