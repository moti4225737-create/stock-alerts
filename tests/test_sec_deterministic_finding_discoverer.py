from unittest.mock import Mock

from models.source_document import SourceDocument
from models.source_finding_candidate import SourceFindingCandidate
from product.sec_deterministic_finding_discoverer import (
    SECDeterministicFindingDiscoverer,
)


def test_sec_deterministic_discoverer_returns_unscored_candidates() -> None:
    signal_extractor = Mock()
    signal_extractor.extract.return_value = {
        "revenue": "increased 18%",
        "cash": "$412 million",
        "net_loss": "$7 million",
    }

    discoverer = SECDeterministicFindingDiscoverer(
        signal_extractor=signal_extractor,
    )

    document = SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="10-Q",
        text=(
            "Revenue increased 18%. "
            "Cash and cash equivalents were $412 million. "
            "Net loss was $7 million."
        ),
    )

    candidates = discoverer.discover(document)

    assert len(candidates) == 3
    assert all(
        isinstance(candidate, SourceFindingCandidate)
        for candidate in candidates
    )

    assert {
        candidate.statement
        for candidate in candidates
    } == {
        "Revenue increased 18%.",
        "Cash and cash equivalents were $412 million.",
        "Net loss was $7 million.",
    }

    assert all(
        candidate.evidence
        for candidate in candidates
    )

    signal_extractor.extract.assert_called_once_with(
        document.text
    )


def test_sec_deterministic_discoverer_ignores_non_sec_documents() -> None:
    signal_extractor = Mock()

    discoverer = SECDeterministicFindingDiscoverer(
        signal_extractor=signal_extractor,
    )

    document = SourceDocument(
        source="FDA",
        source_url="https://www.fda.gov/example",
        title="FDA Update",
        text="Regulatory update",
    )

    assert discoverer.discover(document) == ()
    signal_extractor.extract.assert_not_called()
